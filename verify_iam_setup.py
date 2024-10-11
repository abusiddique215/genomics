import boto3
import json
from botocore.exceptions import ClientError

def verify_iam_setup():
    iam = boto3.client('iam')
    sts = boto3.client('sts')
    role_name = "GenomicsAPIRole"
    user_name = "genomics-api-user"

    print("Verifying IAM setup...")

    # Check if the role exists
    try:
        role = iam.get_role(RoleName=role_name)
        print(f"✅ Role '{role_name}' exists.")
    except ClientError as e:
        print(f"❌ Role '{role_name}' does not exist or is not accessible.")
        return

    # Check if the user can assume the role
    try:
        sts.assume_role(RoleArn=role['Role']['Arn'], RoleSessionName="TestSession")
        print(f"✅ User can assume the '{role_name}' role.")
    except ClientError as e:
        print(f"❌ User cannot assume the '{role_name}' role.")

    # Check if the necessary policies are attached to the role
    try:
        attached_policies = iam.list_attached_role_policies(RoleName=role_name)['AttachedPolicies']
        required_policies = ["AmazonS3FullAccess", "AmazonDynamoDBFullAccess"]
        for policy in required_policies:
            if any(p['PolicyName'] == policy for p in attached_policies):
                print(f"✅ Policy '{policy}' is attached to the role.")
            else:
                print(f"❌ Policy '{policy}' is not attached to the role.")
    except ClientError as e:
        print(f"❌ Unable to list policies for role '{role_name}'.")

    # Check if the user has permission to assume the role
    try:
        user_policies = iam.list_user_policies(UserName=user_name)['PolicyNames']
        inline_policy_found = False
        for policy_name in user_policies:
            policy = iam.get_user_policy(UserName=user_name, PolicyName=policy_name)['PolicyDocument']
            if any(statement.get('Action') == 'sts:AssumeRole' and 
                   statement.get('Resource') == role['Role']['Arn'] 
                   for statement in policy['Statement']):
                inline_policy_found = True
                break
        
        if inline_policy_found:
            print(f"✅ User '{user_name}' has the necessary inline policy to assume the role.")
        else:
            print(f"❌ User '{user_name}' does not have the necessary inline policy to assume the role.")
    except ClientError as e:
        print(f"❌ Unable to check policies for user '{user_name}'.")

if __name__ == "__main__":
    verify_iam_setup()