from .softwares import GenericSoftware, PypiSoftware, GithubSoftware, BitbucketSoftware
from .packages import AurPackage, ArchPackage


class SoftwareTable(prettytable.PrettyTable):
    def add_software_row(self, pkg, src):
        if src.version > pkg.version:
            status = 'UPDATE'
        else:
            status = 'OK'
        self.add_row([pkg.name, src.name,
                      pkg.version, src.version,
                      status])

def main():
    table = SoftwareTable(['PACKAGE', 'PROJECT', 'AUR', 'UPSTREAM', 'STATUS'])

    for name in ['click', 'docker-py', 'pluginbase']:
        aur = AurPackage('python2-' + name.rstrip('-py'), upstream=name)
        pypi = PypiSoftware(name)
        table.add_software_row(aur, pypi)

    table.add_software_row(AurPackage('supernova'),
                           PypiSoftware('supernova'))

    mint_x_icons_pkg = AurPackage('mint-x-icons')
    mint_x_icons_src = GenericSoftware('mint-x-icons',
        url='http://packages.linuxmint.com/pool/main/m/mint-x-icons/')
    table.add_software_row(mint_x_icons_pkg, mint_x_icons_src)

    mint_x_theme_pkg = AurPackage('mint-x-theme', upstream='mint-themes')
    mint_x_theme_src = GenericSoftware('mint-themes',
        url='http://packages.linuxmint.com/pool/main/m/mint-themes/')
    table.add_software_row(mint_x_theme_pkg, mint_x_theme_src)

    autokey_data_xdg_pkg = AurPackage('autokey-data-xdg', upstream='autokey')
    autokey_data_xdg_src = GenericSoftware('autokey',
        url='https://code.google.com/p/autokey/downloads/list')
    table.add_software_row(autokey_data_xdg_pkg, autokey_data_xdg_src)

    print(table)


if __name__ == '__main__':
    main()
