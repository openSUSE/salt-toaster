kill -9 $(pgrep salt-master); kill -9 $(pgrep salt-api); salt-master -l debug -d; salt-api -l debug -d
