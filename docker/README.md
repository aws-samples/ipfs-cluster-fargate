# Dockerfiles to customize ipfs

We have two Dockerfiles that build custom images from the official ipfs:latest Docker image

## Dockerfile: EFS

The `Dockerfile_efs` file provides a customer entrypoint for our Docker container.

The new entrypoints cleans up temporary lock files that IPFS leaves behind.

We also copy the `001-config_efs.sh` shell script to help cleanup the file. You can manipulate IPFS configuration there as well.

## Dockerfile: S3 Plugin

The `Dockerfile_s3` file builds IPFS and the `go-ds-s3` plugin together using the same golang version.
It copies the relevant files to the final Docker image.

We also copy the `001-config_s3.sh` shell script to manipulate the IPFS config file before startup.

### Config changes

The script injects the correct config in the `Datastore.Spec` object to setup the plugin and
update the `datastore_spec` file to reflect the new datastore configuration.

Edit the `001-config_s3.sh` to fit your use case.

### IPFS Config changes

The script injects the correct config in the `Datastore.Spec` object to setup the plugin and
update the `datastore_spec` file to reflect the new datastore configuration.

Edit the `001-config_s3.sh` to fit your use case.

## Building images

Basic build:

```
cd docker
docker build -t my-ipfs-image -f Dockerfile_s3 .
```

Build (Useful command to build AMD64 on ARM based CPUs), tag and push a Docker image for AMD64 architecture to a public AWS ECR repository :

```
docker buildx build --no-cache --platform linux/amd64 -t ipfs-efs -f Dockerfile_efs .
docker tag ipfs-efs:latest public.ecr.aws/k1j0v0i7/ipfs-efs
docker push public.ecr.aws/k1j0v0i7/ipfs-efs
```

## Running a container

```
export ipfs_staging=/local/data/ipfs_staging
export ipfs_data=/local/data/ipfs_data
docker run -d -v $ipfs_staging:/export -v $ipfs_data:/data/ipfs -p 4001:4001 -p 4001:4001/udp -p 127.0.0.1:8080:8080 -p 127.0.0.1:5001:5001 --env-file .env my-ipfs-image`
```

Note that we pass a `.env` file that contains the following environment variables:

```
AWS_REGION=<my_region>
CLUSTER_S3_BUCKET=<my_bucket>
CLUSTER_PEERNAME=<node_name>
CLUSTER_AWS_KEY=<aws_key>
CLUSTER_AWS_SECRET=<aws_secret>
```
