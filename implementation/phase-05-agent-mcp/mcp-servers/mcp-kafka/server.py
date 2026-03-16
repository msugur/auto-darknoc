"""
Dark NOC — Kafka MCP Server
==============================
FastMCP 3.0.2 server for Kafka operations.
Allows the LangGraph agent to read from topics and produce messages.

TOOLS PROVIDED:
    consume_topic      → Read recent messages from a topic
    produce_message    → Write a message to a topic
    get_consumer_lag   → Check consumer group lag
    list_topics        → List all available topics

TRANSPORT: Streamable HTTP on port 8003
"""

import os
import json
from datetime import datetime, timezone
from fastmcp import FastMCP
from kafka import KafkaConsumer, KafkaProducer
from kafka.structs import TopicPartition

mcp = FastMCP(
    name="dark-noc-kafka",
    instructions=(
        "Kafka streaming tools for the Dark NOC agent. "
        "Use consume_topic to read recent messages for analysis. "
        "Use produce_message to send remediation events or audit records. "
        "Use get_consumer_lag to check if the agent is keeping up with log volume."
    ),
)

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "dark-noc-kafka-kafka-bootstrap.dark-noc-kafka.svc:9092")


@mcp.tool()
def consume_topic(
    topic: str,
    max_messages: int = 20,
    timeout_ms: int = 5000,
) -> dict:
    """
    Read recent messages from a Kafka topic.

    Args:
        topic:       Kafka topic name (e.g., "nginx-logs", "noc-alerts")
        max_messages: Maximum number of messages to return (default: 20)
        timeout_ms:  Consumer poll timeout in ms (default: 5000)

    Returns:
        Dict with messages list: [{offset, timestamp, value}]
    """
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        auto_offset_reset="latest",
        enable_auto_commit=False,     # Don't commit — agent is just reading
        consumer_timeout_ms=timeout_ms,
        value_deserializer=lambda m: m.decode("utf-8", errors="replace"),
    )

    messages = []
    try:
        # Seek to end then back max_messages
        consumer.poll(timeout_ms=1000)  # Trigger partition assignment
        partitions = consumer.assignment()

        for tp in partitions:
            end_offset = consumer.end_offsets([tp])[tp]
            start_offset = max(0, end_offset - max_messages)
            consumer.seek(tp, start_offset)

        for msg in consumer:
            try:
                value = json.loads(msg.value)
            except json.JSONDecodeError:
                value = msg.value

            messages.append({
                "partition": msg.partition,
                "offset": msg.offset,
                "timestamp": datetime.fromtimestamp(
                    msg.timestamp / 1000, tz=timezone.utc
                ).isoformat(),
                "value": value,
            })

            if len(messages) >= max_messages:
                break
    finally:
        consumer.close()

    return {
        "topic": topic,
        "messages": messages,
        "count": len(messages),
    }


@mcp.tool()
def produce_message(
    topic: str,
    message: dict,
    key: str = "",
) -> dict:
    """
    Produce a message to a Kafka topic.

    Args:
        topic:   Target topic (e.g., "noc-alerts", "remediation-jobs", "incident-audit")
        message: Dict to serialize as JSON and send
        key:     Optional message key (for partitioning)

    Returns:
        Dict with delivery confirmation
    """
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        key_serializer=lambda k: k.encode("utf-8") if k else None,
        acks="all",    # Wait for all replicas to acknowledge
    )

    try:
        future = producer.send(
            topic,
            value=message,
            key=key if key else None,
        )
        record_metadata = future.get(timeout=10)
        producer.flush()
    finally:
        producer.close()

    return {
        "success": True,
        "topic": record_metadata.topic,
        "partition": record_metadata.partition,
        "offset": record_metadata.offset,
    }


@mcp.tool()
def get_consumer_lag(group_id: str = "dark-noc-agent", topic: str = "nginx-logs") -> dict:
    """
    Get the current consumer lag for a consumer group.
    High lag means the agent is falling behind on processing logs.

    Args:
        group_id: Consumer group ID (default: dark-noc-agent)
        topic:    Topic to check lag for (default: nginx-logs)

    Returns:
        Dict with lag per partition and total lag
    """
    consumer = KafkaConsumer(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        group_id=group_id,
        enable_auto_commit=False,
    )

    try:
        tp_list = [TopicPartition(topic, p)
                   for p in consumer.partitions_for_topic(topic) or [0]]

        # Get end offsets (latest)
        end_offsets = consumer.end_offsets(tp_list)

        # Get committed offsets (what the group has processed)
        committed = {tp: consumer.committed(tp) for tp in tp_list}

        partitions = []
        total_lag = 0
        for tp in tp_list:
            end = end_offsets[tp]
            committed_offset = committed[tp] or 0
            lag = max(0, end - committed_offset)
            total_lag += lag
            partitions.append({
                "partition": tp.partition,
                "end_offset": end,
                "committed_offset": committed_offset,
                "lag": lag,
            })
    finally:
        consumer.close()

    return {
        "group_id": group_id,
        "topic": topic,
        "total_lag": total_lag,
        "partitions": partitions,
        "status": "healthy" if total_lag < 100 else "behind",
    }


@mcp.tool()
def list_topics() -> dict:
    """
    List all available Kafka topics with message counts.

    Returns:
        Dict with topics list: [{name, partitions, latest_offset}]
    """
    consumer = KafkaConsumer(bootstrap_servers=KAFKA_BOOTSTRAP)
    try:
        metadata = consumer.list_consumer_group_offsets
        topics = list(consumer.topics())
        result = []
        for topic in sorted(topics):
            if topic.startswith("_"):   # Skip internal topics
                continue
            partitions = consumer.partitions_for_topic(topic) or set()
            result.append({"name": topic, "partitions": len(partitions)})
    finally:
        consumer.close()

    return {"topics": result, "count": len(result)}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8003"))
    uvicorn.run(mcp.http_app(), host="0.0.0.0", port=port)
