# Run this script to generate bills
#...................................................
#                   START
#......................................................
echo 'installing the python libraries necessary to run this script'
echo ''
python -m pip install --user --upgrade pip
echo 'installing virtual env '
python -m pip install --user virtualenv
echo 'setting up the virtual env'
unameOut="$(uname -s)"
case "${unameOut}" in
    Linux*)     machine=Linux;;
    Darwin*)    machine=Mac;;
    CYGWIN*)    machine=Cygwin;;
    MINGW*)     machine=MinGw;;
    *)          machine="UNKNOWN:${unameOut}"
esac
echo ${machine}
if [ "$machine" == "MinGw" ];then
.\env\Scripts\activate
where python
else
source env/bin/activate
which python
fi
echo 'moving to the appropriate folder'
cd src/
echo 'running the script'
python cashCalls.py