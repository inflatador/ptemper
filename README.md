# ptemper

## Use Case

Need a quick way to download or upload a file without installing software or leaving
credentials around? ptemper creates secure, auth-free, time-limited, download or
upload URLs using Rackspace Cloud Files TempURLs.

## Invoking

ptemper needs five arguments in order. They are:

- Method: HTTP method (GET or PUT).

- Time to live expressed in minutes (M), hours (H), or days (D).

- Datacenter: Rackspace cloud datacenter in which to create the URL. For example:IAD 
(N. Virginia), SYD (Sydney), etc.

- Container name: The Rackspace Cloud Files container to use. If you specify "PUT" as your
HTTP verb, the container must not already exist. If you specify "GET" as your HTTP verb, 
but the container does not already exist, ptemper will output an error and quit.

- Cloud Files Object Name: In other words, the name of the file you wish to download
or upload. If you specify "GET" as your HTTP verb and the object does not already exist,
ptemper will output an error and quit.


## Usage
 
```bash
example command: ./ptemper.py PUT 40M syd my_container my_object.gz
```

example output:

```bash
Container my_container does not already exist. Creating.

Your new tempURL is https://storage101.syd2.clouddrive.com/v1/MossoCloudFS_c59fd903-9564-4b31-88d6-0f1fa7f92eb3/my_container/my_object.gz?temp_url_sig=492d33ed3599ee5d2ad536d32550cbd281a8360d&temp_url_expires=1504914091

Your tempURL expires at 2017-11-30 16:49:32.848003 localtime

example commands:

curl -vX PUT "https://storage101.syd2.clouddrive.com/v1/MossoCloudFS_c59fd903-9564-4b31-88d6-0f1fa7f92eb3/my_container/my_object.gz?temp_url_sig=492d33ed3599ee5d2ad536d32550cbd281a8360d&temp_url_expires=1504914091" --data-binary @my_object.gz

curl -vX PUT "https://snet-storage101.syd2.clouddrive.com/v1/MossoCloudFS_c59fd903-9564-4b31-88d6-0f1fa7f92eb3/my_container/my_object.gz?temp_url_sig=492d33ed3599ee5d2ad536d32550cbd281a8360d&temp_url_expires=1504914091" --data-binary @my_object.gz

Remember, curl tries to put the entire file into memory before copying! Don't oom!
```
## Caveats

Remember that cURL tries to copy the entire file into memory before uploading. If 
you don't have enough memory, your server could OOM.

ptemper was not designed for uploading large objects (objects over 5 GB) and this
feature will not be added.
