# Create JIRA Transition Evidence from the build CI and attach it to the build info
JIRA is an important tool for tracking issues and managing projects and holds all requirements for software changes as Tasks.
For compliant software development, it is important to track requirements review and approval process as these confirm proper approval for code changes done and released.
To allow automation of proper requirements review and approval, we create an evidence of any JIRA linked to the code commits during the build with confirmation it went through approval status before code was committed. 
Every company defines a different approval status, so in our example we allow the calling code send the name of the transition that shold be checked. 

pre-requisites:
1. Hold a cloud JIRA server (for selfhosted jira server, few code adjustments are required)
2. Allow network access from your CI server to Jira server
3. Define few environment variables: jira_url, jira_token, jira_username
4. Commit comments must include the JIRA issue ID (e.g. <jira-project-key>-1234)

The example is based on the following steps:
1. get the relevant commit IDs
2. extract the JIRA IDs from all the build commits
3. call the jira-transition-checker utility (use the binary for your build platform) with these arguments: "transition name" JIRA-ID [,JIRA-ID]
for example:
 ``./examples/jira-transition-example/bin/jira-transition-checker-linux-amd64 "Finance Approval" JIRA-486 PROJ-111 > predicate.json``
optional arg: `--failOnMissingTransition` whihc will fail the script if any of the JIRA IDs sent did not pass the transition check 
4. call the evidence create cli with the predicate.json file
for example:
``jf evd create \
                  --build-name "${{ env.BUILD_NAME }}" \
                  --build-number "${{ github.run_number }}" \
                  --predicate ./predicate.json \
                  --predicate-type https://jfrog.com/evidence/requirements-approval/v1 \
                  --key "${{ secrets.JIRA_TEST_PKEY }}" \
                  --key-alias ${{ vars.JIRA_TEST_KEY }}``



