# Tempertemper

## Use Case

Need a quick way to download or upload a file without installing software or leaving
credentials around? Tempertemper creates and outputs secure, auth-free, time-limited, download or
upload URLs using Rackspace Cloud Files TempURLs.

## Invoking

tempertemper needs five arguments in order. They are:

- Verb: HTTP verb (aka method). Use "GET" for download, "PUT" for upload, or "BOTH" for
both "GET" and "PUT".

- Time 

- Datacenter: Rackspace cloud datacenter in which to create the URL. Valid choices are:
ORD (Chicago), DFW (Dallas/Fort Worth), IAD (N. Virginia), SYD (Sydney), HKG (Hong Kong),
or LON (London). Note that US-based accounts have access to all DCs except LON, while UK-
based accounts have access to LON and no other datacenters. 

- Container name: The Rackspace Cloud Files container to use. If you specify "PUT" or 
"BOTH" as your HTTP verb, the container will be created if it does not already exist. If
you specify "GET" as your HTTP verb, but the container does not already exist, 
tempertemper will output an error and quit.

- Cloud Files Object Name: In other words, the name of the file you wish to download
or upload. If you specify "GET" as your HTTP verb and the file does not already exist,
tempertemper will output an error and quit.

## Caveats

Remember that cURL tries to copy the entire file into memory before uploading. If 
you don't have enough memory, your server could OOM.

Tempertemper was not designed for uploading large objects (objects over 5 GB) and this
feature will not be added.


## Usage
 
```bash
example command: ./tempertemper.py put syd my_container my_compressed_file.gz
```

example output:

```bash
Container my_container does not already exist. Creating.

Your new tempURL is https://storage101.syd2.clouddrive.com/v1/MossoCloudFS_c59fd903-9564-4b31-88d6-0f1fa7f92eb3/my_container/pcap.gz?temp_url_sig=492d33ed3599ee5d2ad536d32550cbd281a8360d&temp_url_expires=1504914091

example commands:

curl -X PUT "https://storage101.syd2.clouddrive.com/v1/MossoCloudFS_c59fd903-9564-4b31-88d6-0f1fa7f92eb3/my_container/pcap.gz?temp_url_sig=492d33ed3599ee5d2ad536d32550cbd281a8360d&temp_url_expires=1504914091" --data-binary @pcap.gz

curl -X PUT "https://snet-storage101.syd2.clouddrive.com/v1/MossoCloudFS_c59fd903-9564-4b31-88d6-0f1fa7f92eb3/my_container/pcap.gz?temp_url_sig=492d33ed3599ee5d2ad536d32550cbd281a8360d&temp_url_expires=1504914091" --data-binary @pcap.gz

Remember, curl tries to put the entire file into memory before copying! Don't oom!
```
