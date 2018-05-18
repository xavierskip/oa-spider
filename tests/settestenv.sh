dir=`pwd`
parentdir="$(dirname "$dir")"
export PYTHONPATH=$parentdir:$PYTHONPATH
echo $PYTHONPATH