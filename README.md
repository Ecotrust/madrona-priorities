# Madrona Prioritization Tool

[Ecotrust](http://ecotrust.org),
in partnership with USFW, the NPLCC and BLM, 
have developed a framework for developing heurstic-based prioritization tools.

The priorities tool is based on Madrona and Marxan. 

It is designed so that the code could be easily repurposed for other projects...

## Updating the dataset for an existing priorties tool

See [Process for loading new dataset](https://github.com/Ecotrust/madrona-priorities/wiki/Process-for-loading-new-dataset)
## To launch a new priorities tool.

* **Spatial data prep**. Decide on polygon planning units and summarize targets and costs to the planning units. See `docs/data_prep.md`

* Clone the **git repository** and create a new branch

```
cd /usr/local/apps/src
git clone git@github.com:Ecotrust/madrona-priorities.git <NEW_PROJECT_NAME> 
cd <NEW_PROJECT_NAME>
git branch <NEW_PROJECT_NAME>
git checkout <NEW_PROJECT_NAME> 
git push -u origin <NEW_PROJECT_NAME> 
```

* **Customize** the global settings, fixtures, etc for this project (and commit them to the project branch). Test locally.

* **Deploy** the initial installation; a virtualenv, madrona, python dependencies, postgres, django etc. (see `docs/INSTALL.md`)

* Import the dataset and deploy subsequent **Updates** to the code or dataset using fabric (see `docs/updating.txt`)

### Customization


* Modify code in the `master` branch to **add new features**. Keep the commits atomic and merge/cherry-pick back into project branches as needed.  Merge carefully and don't bring merge over any project-specific changes.

* Modify the project branches for **project-specific tweaks**. Don't push these changes back into the `master` branch.
* 

## Examples
* http://aquatics-blm.labs.ecotrust.org/
* http://juniper.labs.ecotrust.org/
* http://nplcc.labs.ecotrust.org/
* http://aquatic-priorities.apps.ecotrust.org/
