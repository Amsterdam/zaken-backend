# Release a new version of AZA-backend

To deploy a new version of AZA-backend you need to push a ....
tag to Github. Jenkins will create

We usually release from the master-branch. Create a new tag
with a semantic version number of format "v.x.x.x".
To see the latest tags use

```
git checkout master
git pull
git tag -l | tail
```

To push a new tag to Github, execute:

```
export VERSION=v.x.x.x
git tag $VERSION
git push origin $VERSION
```

Wait for Jenkins to build and deploy the new containers.
https://ci.secure.amsterdam.nl/job/fixxx/job/zaken-backend/view/tags/

If deployment is succesfull you can check the health endpoint
https://api.wonen.zaken.amsterdam.nl/health/
