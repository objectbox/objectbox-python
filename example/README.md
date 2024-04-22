# ObjectBox-Python Examples

The following examples are available from this repository.

## Application Example: Tasks

```
cd example
python -m tasks

Welcome to the ObjectBox tasks-list app example. Type help or ? for a list of commands.
> new buy oat
> new buy yeast
> new bake bread
> ls
 ID  Created                        Finished                       Text
  1  Mon Apr 22 11:02:27 2024                                      buy oat
  2  Mon Apr 22 11:02:30 2024                                      buy yeast
  3  Mon Apr 22 11:02:34 2024                                      bake bread
> done 1
> done 2
> ls
> ls
 ID  Created                        Finished                       Text
  1  Mon Apr 22 11:02:27 2024       Mon Apr 22 11:03:02 2024       buy oat
  2  Mon Apr 22 11:02:30 2024       Mon Apr 22 11:03:18 2024       buy yeast
  3  Mon Apr 22 11:02:34 2024                                      bake bread
> exit
```

