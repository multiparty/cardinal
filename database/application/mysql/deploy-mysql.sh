kubectl apply -f mysql-deployment.yaml
kubectl apply -f mysql-pv.yaml
kubectl run -it --rm --image=mysql:5.6 --restart=Never mysql-client -- mysql -h mysql -ppassword
CREATE DATABASE cardinal;
