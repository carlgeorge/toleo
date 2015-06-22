import toleo
import asyncio
import prettytable


class SoftwareTable(prettytable.PrettyTable):
    def add_software_row(self, u, d):
        if u.version > d.version:
            status = 'UPDATE'
        else:
            status = 'OK'
        self.add_row([d.name,
                      d.version,
                      u.version,
                      status])


# pypi to aur
softwares = [toleo.Relationship(toleo.PypiSource('click'),        toleo.AurPackage('python-click')),
             toleo.Relationship(toleo.PypiSource('mkdocs'),       toleo.AurPackage('mkdocs')),
             toleo.Relationship(toleo.PypiSource('supernova'),    toleo.AurPackage('supernova'))]

# aur to cwg
#softwares = [toleo.Relationship(toleo.AurPackage('python-click'), toleo.ArchPackage('python-click', 'cwg')),
#             toleo.Relationship(toleo.AurPackage('mkdocs'),       toleo.ArchPackage('mkdocs', 'cwg')),
#             toleo.Relationship(toleo.AurPackage('supernova'),    toleo.ArchPackage('supernova', 'cwg'))]

tasks = [s._load() for s in softwares]

loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.wait(tasks))
loop.close()


table = SoftwareTable(['NAME', 'VERSION', 'UPSTREAM', 'STATUS'])
for software in softwares:
    table.add_software_row(software.upstream,
                           software.downstream)

print(table)
