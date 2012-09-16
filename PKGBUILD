# Maintainer: Tom Wallroth
pkgname=python-cherrymusic
pkgver=0.2
pkgrel=1
pkgdesc="an mp3 server for your browser"
arch=('any')
url="http://fomori.org/cherrymusic"
license=('GPL')
groups=()
makedepends=('python')
depends=('python>=3' 'python-cherrypy>=3')
source=()
noextract=()
md5sums=()

build() {
    tar xvf $startdir/CherryMusic-$pkgver.tar.gz
    cd ./CherryMusic-$pkgver
    python ./setup.py install --root=$pkgdir --optimize=1
}
