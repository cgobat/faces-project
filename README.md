# faces-project
*Note: the information provided in this readme is almost entirely outdated and very little of it still applies. This is the information as it is presented\* on [SourceForge](https://sourceforge.net/projects/faces-project/), which was last updated in 2008. I believe that "I" from here on in this documentation refers to [@aannoo](mailto:aanno@users.sourceforge.net).*

\*I have updated it to be markdown-compliant and made some formatting changes, but that is all.

---

Homepage: ~~<http://faces.homeip.net>~~ (dead link)

faces is licenced under the GPL (<http://www.gnu.org/copyleft/gpl.html>). 

faces is a powerful and free project management tool. faces stands for **f**lexible, **a**utomated, **c**alculating, **e**xtendible, **s**imulating. It is based on python, an easy to learn and powerful programming language.

Anybody who is tired spending hours of trying to get your project data into a software tool, that offers limited functionality. In faces project plans are defined by simple python programs, which are indeed plain text files. Creating and restructuring project plans is much faster than any grid or formular based method could be. The whole concept of faces aims to reduce your time, you have to spend for working on your project management tool. As project manager you need your time for managing your project, not your tool. 

## git repository

This is a public git repo of faces used to speed-up migration to new versions of matplotlib. As a such it *is* a (friendly) fork of [Michael Reithinger](https://sourceforge.net/u/mreithinger/profile/)'s code.

Every contribution would be wellcome. The URL is: <http://repo.or.cz/w/faces-project.git> 

If you register as new user at <http://repo.or.cz/m/reguser.cgi> I could grant you write access if you drop me an eMail (read access is possible without registration). 

Alternatively, you could use the 'mob' account to work on the 'mob' branch. See <http://repo.or.cz/mob.html> for details. 

## git short intro

You could read more about git at <http://git.or.cz/>. 

To check out the repo, use 

    git clone git+ssh://<account_name>@repo.or.cz/srv/git/faces-project.git

To switch to the 'mob' branch, use 

    git checkout mob


## Branches

At present, there are the following branches:
| Name | Description |
| ---- | ----------- |
| master | general improvements (but no matplotlib update stuff) |
| matplotlib91 | towards a faces-project version running on matplotlib 0.91.4 |
| mob | same as matplotlib91 but writable for everyone (see above) |
