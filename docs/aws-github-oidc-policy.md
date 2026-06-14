# AWS OIDC For GitHub Actions

GitHub Actions should assume a short-lived AWS role through OpenID Connect
(OIDC). This avoids storing static AWS access keys in GitHub.

## Trust Relationship

Create the GitHub OIDC provider in AWS IAM with:

- Provider URL: `https://token.actions.githubusercontent.com`
- Audience: `sts.amazonaws.com`

Create an IAM role and scope its trust policy to this repository and the `main`
branch. Replace `ACCOUNT_ID` only where an account ID is required; do not commit
a real account ID to this repository.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
          "token.actions.githubusercontent.com:sub": "repo:scottiepowell/cookbook-roadmaps-link:ref:refs/heads/main"
        }
      }
    }
  ]
}
```

Do not broaden the subject to all repositories or branches. If GitHub
environments are added later, update the subject condition to the exact
environment identity and keep equivalent repository restrictions.

## Workflow Role Permissions

The workflow role needs permission to inspect, start, and stop only the target
EC2 instance, send the AWS-managed SSM shell document to that instance, and
read command results. Replace `AWS_REGION`, `ACCOUNT_ID`, and
`EC2_INSTANCE_ID` when creating the policy in AWS.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ControlCookbookInstance",
      "Effect": "Allow",
      "Action": [
        "ec2:StartInstances",
        "ec2:StopInstances"
      ],
      "Resource": "arn:aws:ec2:AWS_REGION:ACCOUNT_ID:instance/EC2_INSTANCE_ID"
    },
    {
      "Sid": "DescribeEc2AndSsmState",
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:DescribeInstanceStatus",
        "ssm:DescribeInstanceInformation"
      ],
      "Resource": "*"
    },
    {
      "Sid": "RunShellCommand",
      "Effect": "Allow",
      "Action": "ssm:SendCommand",
      "Resource": [
        "arn:aws:ssm:AWS_REGION::document/AWS-RunShellScript",
        "arn:aws:ec2:AWS_REGION:ACCOUNT_ID:instance/EC2_INSTANCE_ID"
      ]
    },
    {
      "Sid": "ReadCommandResults",
      "Effect": "Allow",
      "Action": [
        "ssm:GetCommandInvocation",
        "ssm:ListCommandInvocations"
      ],
      "Resource": "*"
    }
  ]
}
```

The `Describe` and command-result APIs do not support useful resource-level
scoping, so those statements require `Resource: "*"`.
`ec2:DescribeInstanceStatus` is additional to the task's base permission list
because the AWS CLI `instance-status-ok` waiter calls that API to verify both
EC2 system and instance health checks. No other AWS API permissions are required
by the current workflow.

Store the role ARN as the GitHub Actions secret `AWS_ROLE_ARN`. The ARN is used
by `aws-actions/configure-aws-credentials@v4`; no access-key secrets should be
created.

## EC2 Instance Role

The EC2 instance needs its own IAM instance profile so the SSM agent can register
and receive commands. Attach `AmazonSSMManagedInstanceCore` (or an equivalent
custom policy), ensure the SSM agent is installed and running, and provide
outbound network access to the required Systems Manager endpoints.

The instance also needs Git, Docker Engine, and the Docker Compose plugin. Its
operating-system user and filesystem permissions must allow SSM Run Command to
manage `/opt/cookbook` and run Docker.
