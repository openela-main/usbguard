%global _hardened_build 1
%global selinuxtype targeted
%global moduletype contrib
%define semodule_version 0.0.4
%define notifier_version 0.0.6

%bcond_without check

Name:           usbguard
Version:        1.0.0
Release:        15%{?dist}
Summary:        A tool for implementing USB device usage policy
Group:          System Environment/Daemons
License:        GPLv2+
## Not installed
# src/ThirdParty/Catch: Boost Software License - Version 1.0
URL:            https://usbguard.github.io/
Source0:        https://github.com/USBGuard/usbguard/releases/download/%{name}-%{version}/%{name}-%{version}.tar.gz
Source1:        https://github.com/USBGuard/%{name}-selinux/archive/v%{semodule_version}.tar.gz#/%{name}-selinux-%{semodule_version}.tar.gz
Source2:        https://github.com/Cropi/%{name}-notifier/releases/download/%{name}-notifier-%{notifier_version}/%{name}-notifier-%{notifier_version}.tar.gz
Source3:        usbguard-daemon.conf
ExcludeArch: i686

Requires: systemd
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd
Requires(post): /sbin/ldconfig
Requires(postun): /sbin/ldconfig
Recommends: (%{name}-selinux if selinux-policy-%{selinuxtype})

BuildRequires: gcc-c++
BuildRequires: libqb-devel
BuildRequires: libgcrypt-devel
BuildRequires: libstdc++-devel
BuildRequires: protobuf-devel protobuf-compiler
BuildRequires: PEGTL-static
BuildRequires: catch1-devel
BuildRequires: autoconf automake libtool
BuildRequires: bash-completion
BuildRequires: asciidoc
BuildRequires: audit-libs-devel
# For `pkg-config systemd` only
BuildRequires: systemd

BuildRequires: dbus-glib-devel
BuildRequires: dbus-devel
BuildRequires: glib2-devel
BuildRequires: polkit-devel
BuildRequires: libxslt
BuildRequires: libxml2

Patch1: usbguard-0.7.6-notifier.patch
Patch2: usbguard-audit-capability.patch
Patch3: usbguard-selinux-audit-capability.patch
Patch4: usbguard-service-pidfile.patch
Patch5: usbguard-ipc-override-fix.patch
Patch6: usbguard-validate-acl.patch
Patch7: usbguard-notifier-decrease-spam.patch
Patch8: usbguard-dbus-CVE.patch
Patch9: usbguard-selinux-dbus-CVE.patch
Patch10: usbguard-dbus-CVE-leak.patch
Patch11: usbguard-OOMScoreAdjust.patch
Patch12: usbguard-daemon-race-condition.patch
Patch13: usbguard-consistent-rules.patch
Patch14: usbguard-missing-doc.patch
Patch15: usbguard-permanent-rules.patch
Patch16: usbguard-disable-console-log.patch

%description
The USBGuard software framework helps to protect your computer against rogue USB
devices by implementing basic whitelisting/blacklisting capabilities based on
USB device attributes.

%package        devel
Summary:        Development files for %{name}
Group:          Development/Libraries
Requires:       %{name} = %{version}-%{release}
Requires:       pkgconfig
Requires:       libstdc++-devel

%description    devel
The %{name}-devel package contains libraries and header files for
developing applications that use %{name}.

%package        tools
Summary:        USBGuard Tools
Group:          Applications/System
Requires:       %{name} = %{version}-%{release}

%description    tools
The %{name}-tools package contains optional tools from the USBGuard
software framework.

%package        dbus
Summary:        USBGuard D-Bus Service
Group:          Applications/System
Requires:       %{name} = %{version}-%{release}
Requires:       dbus
Requires:       polkit

%description    dbus
The %{name}-dbus package contains an optional component that provides
a D-Bus interface to the USBGuard daemon component.

%package        selinux
Summary:        USBGuard selinux
Group:          Applications/System
Requires:       selinux-policy-%{selinuxtype}
Requires(post): selinux-policy-%{selinuxtype}
BuildRequires:  selinux-policy-devel
BuildArch: noarch
%{?selinux_requires}

%description    selinux
The %{name}-selinux package contains selinux policy for the USBGuard
daemon.

%package        notifier
Summary:        A tool for detecting usbguard policy and device presence changes
Group:          Applications/System
Requires:       %{name} = %{version}-%{release}
Requires:       systemd
BuildRequires:  librsvg2-devel
BuildRequires:  libnotify-devel
BuildRequires:  execstack

%description    notifier
The %{name}-notifier package detects usbguard policy modifications as well as
device presence changes and displays them as pop-up notifications.

# usbguard
%prep
%setup -q

# selinux
%setup -q -D -T -a 1

# notifier
%setup -q -D -T -a 2

# Remove bundled library sources before build
rm -rf src/ThirdParty/{Catch,PEGTL}

%patch1 -p1 -b .notifier
%patch2 -p1 -b .audit-write
%patch3 -p1 -b .selinux-audit-write
%patch4 -p1 -b .pidfile
%patch5 -p1 -b .ipc-override-fix
%patch6 -p1 -b .validate-acl
%patch7 -p1 -b .notifier-decrease-spam
%patch8 -p1 -b .dbus-CVE
%patch9 -p1 -b .selinux-dbus-CVE
%patch10 -p1 -b .dbus-CVE-leak
%patch11 -p1 -b .oomscore-adjust
%patch12 -p1 -b .race-condition
%patch13 -p1 -b .consistent-rules
%patch14 -p1 -b .missing-doc
%patch15 -p1 -b .permanent-rules
%patch16 -p1 -b .disable-syslog

%build
mkdir -p ./m4
autoreconf -i -v --no-recursive ./
%configure \
    --disable-silent-rules \
    --without-bundled-catch \
    --without-bundled-pegtl \
    --enable-systemd \
    --with-dbus \
    --with-polkit \
    --with-crypto-library=gcrypt

make %{?_smp_mflags}

# selinux
pushd %{name}-selinux-%{semodule_version}
make
popd

# notifier
pushd %{name}-notifier-%{notifier_version}
mkdir -p ./m4
autoreconf -i -v --no-recursive ./
export CXXFLAGS="$RPM_OPT_FLAGS"
%configure \
    --disable-silent-rules \
    --without-bundled-catch \
    --enable-debug-build \
    --disable-notifier-cli \
    --with-usbguard-devel="../"

%set_build_flags
make %{?_smp_mflags}
popd

%if %{with check}
%check
make check
%endif

# selinux
%pre selinux
%selinux_relabel_pre -s %{selinuxtype}

%install
make install INSTALL='install -p' DESTDIR=%{buildroot}

# Overwrite configuration with distribution defaults
mkdir -p %{buildroot}%{_sysconfdir}/usbguard
mkdir -p %{buildroot}%{_sysconfdir}/usbguard/rules.d
mkdir -p %{buildroot}%{_sysconfdir}/usbguard/IPCAccessControl.d
install -p -m 644 %{SOURCE3} %{buildroot}%{_sysconfdir}/usbguard/usbguard-daemon.conf

# selinux
install -d %{buildroot}%{_datadir}/selinux/packages/%{selinuxtype}
install -m 0644 %{name}-selinux-%{semodule_version}/%{name}.pp.bz2 %{buildroot}%{_datadir}/selinux/packages/%{selinuxtype}
install -d -p %{buildroot}%{_datadir}/selinux/devel/include/%{moduletype}
install -p -m 644 %{name}-selinux-%{semodule_version}/%{name}.if %{buildroot}%{_datadir}/selinux/devel/include/%{moduletype}/ipp-%{name}.if

# notifier
pushd %{name}-notifier-%{notifier_version}
make install INSTALL='install -p' DESTDIR=%{buildroot}
execstack -c %{buildroot}%{_bindir}/%{name}-notifier
popd

# Cleanup
find %{buildroot} \( -name '*.la' -o -name '*.a' \) -exec rm -f {} ';'

%preun
%systemd_preun usbguard.service

%post
/sbin/ldconfig
%systemd_post usbguard.service

%postun
/sbin/ldconfig
%systemd_postun usbguard.service

%files
%defattr(-,root,root,-)
%doc README.adoc CHANGELOG.md
%license LICENSE
%{_libdir}/*.so.*
%{_sbindir}/usbguard-daemon
%{_bindir}/usbguard
%dir %{_localstatedir}/log/usbguard
%dir %{_sysconfdir}/usbguard
%dir %{_sysconfdir}/usbguard/rules.d/
%dir %{_sysconfdir}/usbguard/IPCAccessControl.d
%config(noreplace) %attr(0600,-,-) %{_sysconfdir}/usbguard/usbguard-daemon.conf
%config(noreplace) %attr(0600,-,-) %{_sysconfdir}/usbguard/rules.conf
%{_unitdir}/usbguard.service
%{_datadir}/man/man8/usbguard-daemon.8.gz
%{_datadir}/man/man5/usbguard-daemon.conf.5.gz
%{_datadir}/man/man5/usbguard-rules.conf.5.gz
%{_datadir}/man/man1/usbguard.1.gz
%{_datadir}/bash-completion/completions/usbguard

%files devel
%defattr(-,root,root,-)
%{_includedir}/*
%{_libdir}/*.so
%{_libdir}/pkgconfig/*.pc

%files tools
%defattr(-,root,root,-)
%{_bindir}/usbguard-rule-parser


%files dbus
%defattr(-,root,root,-)
%{_sbindir}/usbguard-dbus
%{_datadir}/dbus-1/system-services/org.usbguard1.service
%{_datadir}/dbus-1/system.d/org.usbguard1.conf
%{_datadir}/polkit-1/actions/org.usbguard1.policy
%{_unitdir}/usbguard-dbus.service
%{_mandir}/man8/usbguard-dbus.8.gz

%preun dbus
%systemd_preun usbguard-dbus.service

%post dbus
%systemd_post usbguard-dbus.service

%postun dbus
%systemd_postun_with_restart usbguard-dbus.service

%files selinux
%{_datadir}/selinux/packages/%{selinuxtype}/%{name}.pp.bz2
%ghost %verify(not md5 size mode mtime) %{_sharedstatedir}/selinux/%{selinuxtype}/active/modules/200/%{name}
%{_datadir}/selinux/devel/include/%{moduletype}/ipp-%{name}.if

%post selinux
%selinux_modules_install -s %{selinuxtype} %{_datadir}/selinux/packages/%{selinuxtype}/%{name}.pp.bz2

%postun selinux
if [ $1 -eq 0 ]; then
    %selinux_modules_uninstall -s %{selinuxtype} %{name}
fi

%posttrans selinux
%selinux_relabel_post -s %{selinuxtype}

%files notifier
%defattr(-,root,root,-)
%doc %{name}-notifier-%{notifier_version}/README.md %{name}-notifier-%{notifier_version}/CHANGELOG.md
%license %{name}-notifier-%{notifier_version}/LICENSE
%{_bindir}/%{name}-notifier
%{_mandir}/man1/%{name}-notifier.1.gz
%{_userunitdir}/%{name}-notifier.service

%post notifier
%systemd_user_post \--preset-mode=disable-only %{name}-notifier.service

%preun notifier
%systemd_user_preun %{name}-notifier.service

%postun notifier
%systemd_user_postun_with_restart %{name}-notifier.service


%changelog
* Thu Jan 12 2023 Attila Lakatos <alakatos@redhat.com> - 1.0.0-15
- Disable logging to console, logging to syslog is still enabled
Resolves: rhbz#2122109
- Store permanent rules even if RuleFile is not set but RuleFolder is
Resolves: rhbz#2155910

* Mon Nov 28 2022 Attila Lakatos <alakatos@redhat.com> - 1.0.0-12
- Set OOMScoreAdjust to -1000 in service file
Resolves: rhbz#2097419
- Fix race condition in usbguard-daemon when forking
Resolves: rhbz#2042345
- Add missing files to documentation
Resolves: rhbz#2122107
- Neither RuleFolder nor RuleFile exists bugfix
Resolves: rhbz#2122109
- Remove build for i686 arch
Resolves: rhbz#2126622

* Tue Aug 16 2022 Attila Lakatos <alakatos@redhat.com> - 1.0.0-11
- Fix unauthorized access via D-bus
- Fix memory leak when connection to dbus is broken
Resolves: rhbz#2059068

* Mon Oct 25 2021 Zoltan Fridrich <zfridric@redhat.com> - 1.0.0-10
- fix DSP module definition in spec file
Resolves: rhbz#2014442
- fix IPC access control files override
Resolves: rhbz#2009227
- validate ACL permission existence
Resolves: rhbz#2009229
- decrease usbguard-notifier spam when denied connection
Resolves: rhbz#2009226

* Tue Aug 10 2021 Mohan Boddu <mboddu@redhat.com> - 1.0.0-8
- Rebuilt for IMA sigs, glibc 2.34, aarch64 flags
  Related: rhbz#1991688

* Wed Jul 28 2021 Radovan Sroka <rsroka@redhat.com> - 1.0.0-7
RHEL 9 BETA
- starting usbguard service complains about PIDFile= references a path below legacy directory /var/run/
Resolves: rhbz#1985627
- file conflict when installing usbguard on rhel
Resolves: rhbz#1986785

* Fri Apr 16 2021 Attila Lakatos <alakatos@redhat.com> - 1.0.0-6
- Clear executable stack flag on usbguard-notifier
Resolves: rhbz#1917544

* Fri Apr 16 2021 Mohan Boddu <mboddu@redhat.com> - 1.0.0-5
- Rebuilt for RHEL 9 BETA on Apr 15th 2021. Related: rhbz#1947937

* Fri Feb 19 2021 Attila Lakatos <alakatos@redhat.com> - 1.0.0-4
- sync with rhel-8.4.0 branch
- bundle usbguard-notifier as subpackage
Resolves: rhbz#1917544

* Wed Jan 27 2021 Fedora Release Engineering <releng@fedoraproject.org> - 1.0.0-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_34_Mass_Rebuild

* Sat Jan 16 12:49:32 CET 2021 Adrian Reber <adrian@lisas.de> - 1.0.0-2
- Rebuilt for protobuf 3.14

* Thu Jan 14 2021 Zoltan Fridrich <zfridric@redhat.com> - 1.0.0-1
- rebase usbguard to 1.0.0
- added support for rules covering combination of classes
- fix usbguard being killed
Resolves: rhbz#1916039
Resolves: rhbz#1861330
Resolves: rhbz#1905257

* Wed Jan 13 14:43:57 CET 2021 Adrian Reber <adrian@lisas.de> - 0.7.8-6
- Rebuilt for protobuf 3.14

* Thu Sep 24 2020 Adrian Reber <adrian@lisas.de> - 0.7.8-5
- Rebuilt for protobuf 3.13

* Wed Jul 29 2020 Fedora Release Engineering <releng@fedoraproject.org> - 0.7.8-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_33_Mass_Rebuild

* Wed Jun 24 2020 Radovan Sroka <rsroka@redhat.com> - 0.7.8-3
- rebase selinux tarball to v0.0.4
- enable forking style in unit file
- set DevicePolicy to closed in unit file
- usbguard prevented from writing conf via dontaudit rule
Resolves: rhbz#1804713
Resolves: rhbz#1789923

* Sun Jun 14 2020 Adrian Reber <adrian@lisas.de> - 0.7.8-2
- Rebuilt for protobuf 3.12

* Tue May 19 2020 Radovan Sroka <rsroka@redhat.com> - 0.7.8-1
- rebase usbguard to 0.7.8
- rebase usbguard-selinux to 0.0.3
- added rules.d/ directory
Resolves: rhbz#1808527

* Fri Jan 31 2020 Fedora Release Engineering <releng@fedoraproject.org> - 0.7.6-8
- Rebuilt for https://fedoraproject.org/wiki/Fedora_32_Mass_Rebuild

* Thu Dec 19 2019 Orion Poplawski <orion@nwra.com> - 0.7.6-7
- Rebuild for protobuf 3.11

* Wed Dec 18 2019 Radovan Sroka <rsroka@redhat.com> - 0.7.6-6
- fix selinux problems

* Mon Dec 02 2019 Radovan Sroka <rsroka@redhat.com> - 0.7.6-5
- obsolete applet-qt subpackage

* Mon Nov 25 2019 Attila Lakatos <alakatos@redhat.com> - 0.7.6-4
- added patch for libqb related permission issues
  resolves: rhbz#1776357
- added patch to ensure that usbguard-daemons is still running after locked screen
  resolves: rhbz#1751861
- added patch to fix permanent device policy changes

* Wed Nov 13 2019 Radovan Sroka <rsroka@redhat.com> - 0.7.6-3
- fixed typo in specfile
- usbguard.conf was generated incorrectly

* Wed Nov 13 2019 Radovan Sroka <rsroka@redhat.com> - 0.7.6-2
- added selinux subpackage

* Mon Nov 11 2019 Radovan Sroka <rsroka@redhat.com> - 0.7.6-1
- rebase to 0.7.6
- removed usbguard-applet subpackage which is not in upstream anymore

* Sat Jul 27 2019 Fedora Release Engineering <releng@fedoraproject.org> - 0.7.2-8
- Rebuilt for https://fedoraproject.org/wiki/Fedora_31_Mass_Rebuild

* Sun Feb 03 2019 Fedora Release Engineering <releng@fedoraproject.org> - 0.7.2-7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_30_Mass_Rebuild

* Wed Nov 21 2018 Igor Gnatenko <ignatenkobrain@fedoraproject.org> - 0.7.2-6
- Rebuild for protobuf 3.6

* Sat Jul 14 2018 Fedora Release Engineering <releng@fedoraproject.org> - 0.7.2-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_29_Mass_Rebuild

* Thu Apr 05 2018 Daniel Kopeček <dkopecek@redhat.com> - 0.7.2-4
- Update to latest PEGTL API

* Fri Feb 09 2018 Fedora Release Engineering <releng@fedoraproject.org> - 0.7.2-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Tue Jan 23 2018 Daniel Kopeček <dkopecek@redhat.com> - 0.7.2-2
- Escape rpm macros mentioned in changelog section

* Tue Jan 23 2018 Daniel Kopeček <dkopecek@redhat.com> - 0.7.2-1
- Update to 0.7.2
- Don't use --enable-werror downstream
- Removed patches related to compiler warnings

* Mon Jan 15 2018 Igor Gnatenko <ignatenkobrain@fedoraproject.org> - 0.7.1-2
- catch → catch1

* Wed Dec 06 2017 Daniel Kopeček <dkopecek@redhat.com> - 0.7.1-1
- Update to 0.7.1

* Wed Nov 29 2017 Igor Gnatenko <ignatenko@redhat.com> - 0.7.0-9
- Rebuild for protobuf 3.5

* Mon Nov 13 2017 Igor Gnatenko <ignatenkobrain@fedoraproject.org> - 0.7.0-8
- Rebuild for protobuf 3.4

* Mon Oct 16 2017 Daniel Kopeček <dkopecek@redhat.com> 0.7.0-7
- Fix enumeration timeout on kernel >= 4.13
  Resolves: rhbz#1499052

* Thu Aug 03 2017 Fedora Release Engineering <releng@fedoraproject.org> - 0.7.0-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Binutils_Mass_Rebuild

* Thu Jul 27 2017 Fedora Release Engineering <releng@fedoraproject.org> - 0.7.0-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Thu Jul 13 2017 Daniel Kopeček <dkopecek@redhat.com> 0.7.0-4
- Added patch to disable unused parameter warning for protobuf
  generated sources to fix compilation with newer protobuf version

* Tue Jun 13 2017 Orion Poplawski <orion@cora.nwra.com> - 0.7.0-3
- Rebuild for protobuf 3.3.1

* Mon May 15 2017 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.7.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_27_Mass_Rebuild

* Thu Apr 13 2017 Daniel Kopeček <dkopecek@redhat.com> 0.7.0-1
- Update to 0.7.0
  - changed PresentDevicePolicy setting from keep to apply-policy
  - added AuditFilePath configuration option pointing to
    /var/log/usbguard/usbguard-audit.log file
  - install bash-completion script
  - use 0600 file permissions for usbguard-daemon.conf and rules.conf

* Sun Mar 19 2017 Daniel Kopeček <dkopecek@redhat.com> 0.6.3-0.1.20170319
- Update to latest git snapshot

* Fri Mar 17 2017 Daniel Kopeček <dkopecek@redhat.com> 0.6.3-0.1.20170317
- Update to latest git snapshot
- Use --enable-werror configure option as the upstream default
  changed to not use -Werror.

* Thu Mar 02 2017 Daniel Kopeček <dkopecek@redhat.com> 0.6.3-0.1.20170301
- Update to latest git snapshot
- Disabled upstream alignment warning compiler flag

* Sat Feb 11 2017 Fedora Release Engineering <releng@fedoraproject.org> - 0.6.2-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Thu Jan 26 2017 Orion Poplawski <orion@cora.nwra.com> - 0.6.2-3
- Rebuild for protobuf 3.2.0

* Sat Nov 19 2016 Orion Poplawski <orion@cora.nwra.com> - 0.6.2-2
- Rebuild for protobuf 3.1.0

* Sun Sep 18 2016 Daniel Kopeček <dkopecek@redhat.com> 0.6.2-1
- Update to 0.6.2

* Fri Sep 16 2016 Daniel Kopeček <dkopecek@redhat.com> 0.6.1-1
- Update to 0.6.1

* Sun Sep 04 2016 Daniel Kopeček <dkopecek@redhat.com> 0.6.0-1
- Update to 0.6.0

* Thu Aug 18 2016 Daniel Kopeček <dkopecek@redhat.com> 0.5.14-1
- Update to 0.5.14

* Tue Aug 16 2016 Daniel Kopeček <dkopecek@redhat.com> 0.5.13-1
- Update to 0.5.13

* Sun Aug 14 2016 Daniel Kopeček <dkopecek@redhat.com> 0.5.12-1
- Update to 0.5.12

* Sat Aug 13 2016 Daniel Kopeček <dkopecek@redhat.com> 0.5.11-2
- Update source tarball
- Ship CHANGELOG.md

* Sat Aug 13 2016 Daniel Kopeček <dkopecek@redhat.com> 0.5.11-1
- Update to 0.5.11
- Use libgcrypt instead of libsodium for crypto

* Thu Jul 21 2016 Daniel Kopecek <dkopecek@redhat.com> 0.5.10-2
- Adjust the default configuration to keep the authorization state
  of present controller devices.

* Sat Jul 09 2016 Daniel Kopecek <dkopecek@redhat.com> 0.5.10-1
- Update to release 0.5.10

* Mon Mar 07 2016 Remi Collet <remi@fedoraproject.org> - 0.4-5
- rebuild for new libsodium soname

* Sun Feb 07 2016 Daniel Kopecek <dkopecek@redhat.com> 0.4-4
- Update to version 0.4
- added usbguard CLI
- added a tools subpackage with usbguard-rule-parser binary

* Fri Feb 05 2016 Fedora Release Engineering <releng@fedoraproject.org> - 0.3p3-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Fri Jun 19 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.3p3-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Tue Apr 14 2015 Daniel Kopecek <dkopecek@redhat.com> 0.3p3-1
- Update to version 0.3p3
- added %%check section
- removed explicit -devel requires on systemd, libqb and
  libsodium devel files
- added -devel requires on libstdc++-devel

* Sat Apr 11 2015 Daniel Kopecek <dkopecek@redhat.com> 0.3p2-1
- Update to version 0.3p2
- use system-wide json and spdlog packages

* Fri Apr 10 2015 Daniel Kopecek <dkopecek@redhat.com> 0.3p1-1
- Update to version 0.3p1
- removed bundled cppformat copylib

* Thu Apr 09 2015 Daniel Kopecek <dkopecek@redhat.com> 0.3-1
- Update to version 0.3
- disabled silent rules
- install license file
- added man pages
- use _hardened_build 1 instead of custom compilation flags
- fix file permissions on files in /etc
- do not install an empty rule set file

* Fri Apr 03 2015 Daniel Kopecek <dkopecek@redhat.com> 0.2-1
- Update to version 0.2
- Updated description
- Corrected package group

* Tue Mar 17 2015 Daniel Kopecek <dkopecek@redhat.com> 0.1-1
- Initial package
