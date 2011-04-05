# Copyright 1999-2003 Gentoo Technologies, Inc.
# Distributed under the terms of the GNU General Public License v2
# $Header: Exp $

inherit distutils

DESCRIPTION="easyprompt is a GUI for creating cool bash prompt"
SRC_URI="http://www.sideralis.net/download/${P}.tar.bz2"
HOMEPAGE="http://www.sideralis.net"


IUSE=""
SLOT="0"
LICENSE="GPL-2"
KEYWORDS="~x86"

DEPEND="
       >=dev-lang/python-2.3.0
       >=x11-libs/gtk+-2.4.0
       >=dev-python/pygtk-2.3.92"

src_install() {
       distutils_src_install
       dodir /usr/bin
       dosym /usr/local/share/EasyPrompt/easyprompt.py /usr/bin/easyprompt
}

pkg_postinst() {
        einfo "Put plugins into ~/.easyprompt/plugins and use them with the \"plug_\" prefix"
}
