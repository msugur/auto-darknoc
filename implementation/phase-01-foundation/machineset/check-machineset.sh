#!/usr/bin/env bash
# =============================================================
# check-machineset.sh — Helper to fill GPU MachineSet placeholders
# =============================================================
# PURPOSE:
#   Extracts the values you need to fill in gpu-worker-machineset.yaml
#   from your existing cluster. Run this on the HUB cluster after
#   logging in with admin credentials.
#
# USAGE:
#   chmod +x check-machineset.sh
#   ./check-machineset.sh
#
# OUTPUT:
#   Prints all placeholder values for gpu-worker-machineset.yaml
# =============================================================
set -euo pipefail

echo "======================================================="
echo " Dark NOC — GPU MachineSet Placeholder Extractor"
echo "======================================================="
echo ""

# 1. Cluster Infrastructure ID
CLUSTER_ID=$(oc get infrastructure cluster -o jsonpath='{.status.infrastructureName}')
echo "✅ CLUSTER_ID (replace <CLUSTER-ID>):"
echo "   ${CLUSTER_ID}"
echo ""

# 2. Find an existing worker MachineSet to get reference values
EXISTING_MS=$(oc get machinesets -n openshift-machine-api -o name | head -1 | cut -d/ -f2)
echo "📋 Using existing MachineSet as reference: ${EXISTING_MS}"
echo ""

# 3. Availability Zone
AZ=$(oc get machineset "${EXISTING_MS}" -n openshift-machine-api \
  -o jsonpath='{.spec.template.spec.providerSpec.value.placement.availabilityZone}')
echo "✅ AVAILABILITY_ZONE (replace <AVAILABILITY-ZONE>):"
echo "   ${AZ}"
echo ""

# 4. AMI ID
AMI_ID=$(oc get machineset "${EXISTING_MS}" -n openshift-machine-api \
  -o jsonpath='{.spec.template.spec.providerSpec.value.ami.id}')
echo "✅ AMI_ID (replace <AMI-ID>):"
echo "   ${AMI_ID}"
echo ""

# 5. Subnet ID
SUBNET_ID=$(oc get machineset "${EXISTING_MS}" -n openshift-machine-api \
  -o jsonpath='{.spec.template.spec.providerSpec.value.subnet.id}')
echo "✅ SUBNET_ID (replace <SUBNET-ID>):"
echo "   ${SUBNET_ID}"
echo ""

# 6. Security Group Name
SG_NAME=$(oc get machineset "${EXISTING_MS}" -n openshift-machine-api \
  -o jsonpath='{.spec.template.spec.providerSpec.value.securityGroups[0].filters[0].values[0]}')
echo "✅ SECURITY_GROUP_NAME (replace <SECURITY-GROUP-NAME>):"
echo "   ${SG_NAME}"
echo ""

# 7. Generate ready-to-use sed command
echo "======================================================="
echo " Ready-to-use sed command (updates the YAML in place):"
echo "======================================================="
echo ""
echo "cd \$(dirname \$0)"
echo "sed -i '' \\"
echo "  -e 's/<CLUSTER-ID>/${CLUSTER_ID}/g' \\"
echo "  -e 's/<AVAILABILITY-ZONE>/${AZ}/g' \\"
echo "  -e 's/<AMI-ID>/${AMI_ID}/g' \\"
echo "  -e 's/<SUBNET-ID>/${SUBNET_ID}/g' \\"
echo "  gpu-worker-machineset.yaml"
echo ""
echo "# Then manually update <SECURITY-GROUP-NAME> if needed:"
echo "# grep -n 'SECURITY-GROUP' gpu-worker-machineset.yaml"
echo ""

# 8. Verify g5.2xlarge availability in this AZ
echo "======================================================="
echo " Verifying g5.2xlarge availability in ${AZ}..."
echo "======================================================="
AWS_REGION=$(oc get infrastructure cluster -o jsonpath='{.status.platformStatus.aws.region}')
echo "Region: ${AWS_REGION}"
echo ""
echo "Run this to check GPU instance availability:"
echo "  aws ec2 describe-instance-type-offerings \\"
echo "    --region ${AWS_REGION} \\"
echo "    --filters Name=instance-type,Values=g5.2xlarge \\"
echo "              Name=location,Values=${AZ} \\"
echo "    --location-type availability-zone \\"
echo "    --query 'InstanceTypeOfferings[].{Type:InstanceType,AZ:Location}' \\"
echo "    --output table"
echo ""
echo "======================================================="
echo " Done. Apply machineset AFTER filling all placeholders:"
echo "   oc apply -f gpu-worker-machineset.yaml"
echo "   watch oc get machines -n openshift-machine-api"
echo "======================================================="
