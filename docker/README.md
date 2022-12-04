# Example Dockerfile to integrate the go-ds-s3 plugin for IPFS

The Dockerfile builds IPFS and the go-ds-s3 plugin together using the same golang version.
It copies the relevant files to the new Docker image.

We also copy the `001-config.sh` shell script to manipulate the IPFS config file before startup.

## Config changes

The init script injects the following config in the `Swarm.ResourceMgr.Limits.System` object:

```
{ 
    Memory: 1073741824, 
    FD: 1024, 
    Conns: 1024, 
    ConnsInbound: 256, 
    ConnsOutboun: 1024, 
    Streams: 16384, 
    StreamsInbound: 4096, 
    StreamsOutbound: 16384 
}
```

The script also inject the correct config in the `Datastore.Spec` object to setup the plugin:

```
{ 
    mounts: [
        {
          child: {
            type: \"s3ds\",
            region: \"${AWS_REGION}\",
            bucket: \"${CLUSTER_S3_BUCKET}\",
            rootDirectory: \"${CLUSTER_PEERNAME}\",
            accessKey: \"${CLUSTER_AWS_KEY}\",
            secretKey: \"${CLUSTER_AWS_SECRET}\"
          },
          mountpoint: \"/blocks\",
          prefix: \"s3.datastore\",
          type: \"measure\"
        },
        {
          child: {
            compression: \"none\",
            path: \"datastore\",
            type: \"levelds\"
          },
          mountpoint: \"/\",
          prefix: \"leveldb.datastore\",
          type: \"measure\"
        }
    ], 
    type: \"mount\"
}
```

## Building the image

`docker build -t my-ipfs-image .`

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

