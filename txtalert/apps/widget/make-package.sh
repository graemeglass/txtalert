#!/bin/bash
mkdir -p package && cd package
wget -m -p http://localhost:8000/widget/
cd "localhost:8000" && sed -e 's/\/static\///' widget/widget.html > index.html
mv static/* .
rmdir static
cp ../../templates/widget/config.xml .
cp ../../static/images/*.png ./images/
rm -rf widget
zip -r ../../widget.wgt .
cd ../..
rm -rf package
