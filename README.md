# Madrona Prioritization Tool

[Ecotrust](http://ecotrust.org),
in partnership with USFW, the NPLCC and BLM, 
have developed a framework for developing heurstic-based prioritization tools.

The priorities tool is based on Madrona and Marxan. 

It is designed so that the code could be easily repurposed for other projects...

## To install a new priorities tool.

* **Spatial data prep**. Decide on polygon planning units and summarize targets and costs to the planning units. See `docs/data_prep.md`

* Clone the **git repository** and create a new branch

```
cd /usr/local/apps/src
git clone git@github.com:Ecotrust/madrona-priorities.git <NEW_PROJECT_NAME> 
git branch <NEW_PROJECT_NAME>
git checkout <NEW_PROJECT_NAME> 
git push -u origin <NEW_PROJECT_NAME> 
```

* **Install** a virtualenv, madrona, python dependencies, postgres, django etc. (see `docs/INSTALL.md`)

* **Import** the data. (see `seak/import.sh`)

### optional

* **Update** the dataset with the import.sh script (see `docs/updating.txt`)

* Modify code in the `master` branch to **add new features**. Keep the commits atomic and merge/cherry-pick back into project branches as needed.  Merge carefully and don't bring merge over any project-specific changes.

* Modify the project branches for **project-specific tweaks**. Don't push these changes back into the `master` branch.
