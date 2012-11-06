# Madrona Prioritization Tool

[Ecotrust](http://ecotrust.org),
in partnership with USFW, the NPLCC and BLM, 
have developed a framework for developing heurstic-based prioritization tools.

The priorities tool is based on Madrona and Marxan. 

It is designed so that the code could be easily repurposed for other projects...

## To install a new priorities tool.

1. **Spatial data prep**. Decide on polygon planning units and summarize targets and costs to the planning units. See `docs/data_prep.md`

2. Clone the **git repository** and create a new branch

```
cd /usr/local/apps/src
git clone git@github.com:Ecotrust/madrona-priorities.git <NEW_PROJECT_NAME> 
git branch <NEW_PROJECT_NAME>
git checkout <NEW_PROJECT_NAME> 
git push -u origin <NEW_PROJECT_NAME> 
```

3. Install a virtualenv, madrona, python dependencies, postgres, django etc. (see `INSTALL.md`)

4. Import the data. (see `seak/import.sh`)

### optional

5. Update the dataset with the import.sh script (see `docs/updating.txt`)

6. Modify code to add features. Do this *in the project branch*, keeping the commits atomic, and merging back into master. 
Merge carefully and don't bring merge over any project-specific changes.
