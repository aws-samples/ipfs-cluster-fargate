# Contributing Guidelines

Thank you for your interest in contributing to our project. Whether it's a bug report, new feature, correction, or additional
documentation, we greatly value feedback and contributions from our community.

Please read through this document before submitting any issues or pull requests to ensure we have all the necessary
information to effectively respond to your bug report or contribution.


## Reporting Bugs/Feature Requests

We welcome you to use the GitHub issue tracker to report bugs or suggest features.

When filing an issue, please check existing open, or recently closed, issues to make sure somebody else hasn't already
reported the issue. Please try to include as much information as you can. Details like these are incredibly useful:

* A reproducible test case or series of steps
* The version of our code being used
* Any modifications you've made relevant to the bug
* Anything unusual about your environment or deployment


## Contributing via Pull Requests
Contributions via pull requests are much appreciated. Before sending us a pull request, please ensure that:

1. You are working against the latest source on the *main* branch.
1. You check existing open, and recently merged, pull requests to make sure someone else hasn't addressed the problem already.
1. You open an issue to discuss any significant work - we would hate for your time to be wasted.

To send us a pull request, please:

### Fork and Clond the repository

[Fork and Clone](https://docs.github.com/en/github/getting-started-with-github/fork-a-repo) the ipfs-cluster-fargate repo.

1. Fork the original ipfs-cluster-fargate repo to create a copy of the repo in your own GitHub account: https://github.com/aws-samples/ipfs-cluster-fargate
1. Clone your copy of the repo to download it locally: `git clone https://github.com/{your-github-username}/ipfs-cluster-fargate.git`
1. Change into the new local directory: `cd ipfs-cluster-fargate`
1. Add the original ipfs-cluster-fargate repo as another remote repo called "upstream": `git remote add upstream https://github.com/aws-samples/ipfs-cluster-fargate`
1. For verification, display the remote repos: `git remote -v`

    The output should look like this:

    ```
	origin  https://github.com/{your-github-username}/ipfs-cluster-fargate.git (fetch)
	origin  https://github.com/{your-github-username}/ipfs-cluster-fargate.git (push)
	upstream        https://github.com/aws-samples/ipfs-cluster-fargate (fetch)
	upstream        https://github.com/aws-samples/ipfs-cluster-fargate (push)
    ```

GitHub provides additional document on [forking a repository](https://help.github.com/articles/fork-a-repo/)

### Create Branch

Create a new local branch for modification being made. This allows you to create separate pull requests in the upstream repo.

1. Create and checkout a new local branch before making code changes: `git checkout -b {branch-name}`
    
1. For verification, display all branches: `git branch -a`

    The output should look like this:

    ```
    * {branch-name}
    main
    remotes/origin/HEAD → origin/main
    remotes/origin/main
    ```

### Your Code

Now is the time to modify existing code.

1. When your code is complete, stage the changes to your local branch: `git add .`
1. Commit the changes to your local branch: `git commit -m 'Comment here'`


### Pull Request

Push your code to the remote repos and [create a pull request](https://docs.github.com/en/github/collaborating-with-issues-and-pull-requests/creating-a-pull-request).

1. Push the local branch to the remote origin repo: `git push origin {branch-name}`

2. Go to the [upstream repo](https://github.com/aws-samples/ipfs-cluster-fargate) in Github and click "Compare & pull request".
    1. Enter an appropriate title
    2. Add a description of the changes. Make sure you associate the request with issue number.
    3. Click "Create pull request".


3. Stay involved in the conversation.

GitHub provides additional document on [creating a pull request](https://help.github.com/articles/creating-a-pull-request/).


### Sync Repos

After your pull request has been accepted into the upstream repo:

1. Switch to your local main branch: `git checkout main`
1. Pull changes that occurred in the upstream repo: `git fetch upstream`
1. Merge the upstream main branch with your local main branch: `git merge upstream/main main`
1. Push changes from you local repo to the remote origin repo: `git push origin main`

### Delete Branches

Delete any unnecessary local and origin branches.

1. Switch to your local main branch: `git checkout main`
1. For verification, display all branches: `git branch -a`
1. Delete any unnecessary local branches: `git branch -d {branch-name}`
1. Delete any unnecessary remote origin branches: `git push origin --delete {branch-name}`

## Finding contributions to work on
Looking at the existing issues is a great way to find something to contribute on. As our projects, by default, use the default GitHub issue labels (enhancement/bug/duplicate/help wanted/invalid/question/wontfix), looking at any 'help wanted' issues is a great place to start.


## Code of Conduct
This project has adopted the [Amazon Open Source Code of Conduct](https://aws.github.io/code-of-conduct).
For more information see the [Code of Conduct FAQ](https://aws.github.io/code-of-conduct-faq) or contact
opensource-codeofconduct@amazon.com with any additional questions or comments.


## Security issue notifications
If you discover a potential security issue in this project we ask that you notify AWS/Amazon Security via our [vulnerability reporting page](http://aws.amazon.com/security/vulnerability-reporting/). Please do **not** create a public github issue.


## Licensing

See the [LICENSE](LICENSE) file for our project's licensing. We will ask you to confirm the licensing of your contribution.
