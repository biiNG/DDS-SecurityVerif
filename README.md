# A formal analysis of DDS Security: ProVerif Model

 ## How to reproduce the results

Under **Linux**, run this command in PowerShell(or cmd) at the directory. ProVerif will give all the result of the code, in **ENC-BASE**. Remember to add the path of ProVerif to the environment PATH.

```shell
proverif  -lib ./lib.pvl -lib ./query.pvl -lib ./attacker.pvl  ./ENC.pv
```

Under **Windows**, please change `/ `to `\`.

In **MAC** case, please change the ` ./ENC.pv` to ` ./MAC.pv`.

In **MP** case, it need to do some change in ENC.pv (or MAC.pv). Please change the ` (* <compromiseScenarios> *)`  to `MaliciousParticipant()` in line 218. Then run the command above.

We have also designed other compromised scenarios, which are included in the `./attacker.pvl`. Some of them maybe too strong to make sense, or just to prove the conditions of certain attacks. Please check and try it in the same way.

You can view the html and graph results of ENC-BASE in the folder `./result`, which is generate by the command below under **Windows**.

```powershell
proverif  -html .\result -lib .\lib.pvl -lib .\query.pvl -lib .\attacker.pvl .\ENC.pv 
```

 ## Parallel analysis

### How to use

The `Paralyzer.py` is the parallel analysis script. You can run it by this command with no problem under **Linux/Windows**.

```sh
python Paralyzer.py
```

Executing this command directly will create **numerous** processes and consume significant memory, so it is advisable to run it on a high-performance computer(with large RAM and multi-core). If you are running it on a personal computer or a laptop, please be sure to **save** any ongoing work to prevent OS crashes and related issues.

The script will handle pv and pvl files, extracting all the queries and attackers, and assembling them into ProVerif commands. Subprocesses will be created for the analysis. The analysis program will generate commands for each query in every possible scenario and create a result folder for each. The analysis program will save the output from ProVerif to files, and after the analysis is complete, it will read the TRUE or FALSE results from the output and additionally save a file named after the analysis results.

The results we got are saved in `./paralyzer-result` folder.

### Details

- **Pool size**: In line 172 of the code, you can choose the number of processes in the process pool. The default pool size is equal to the number of CPU cores, and the program will continuously create new processes to start the analysis until all analyses are completed. Therefore, if you run the `Paralyzer.py` directly, it may cause your laptop to become unresponsive due to the simultaneous execution of multiple CPU-intensive processes. You can set the pool size as follows.

```python
    p = Pool() # the default number of subprocess is the number of cores.
	p2 = Pool(4) # the pool size is 4, and this will not significantly impact the computer's performance.
```

- **Path:** In lines 12 to 18 of the code, the paths to the files required by the program are documented. This includes:

  - the path to ProVerif executable,

  - the path to the lib file,

  - the path to the query file,

  - the path to the main process, 

  - the path to the attacker process, 

  - and the location for saving analysis results. 

    Typically, these do not need to be altered. When using this program for other similar analyses, simply modify the corresponding file paths in the respective directories.

- **Query**: In the `query.pvl` file, all queries are organized in the following format.

  ```
  query 
  (* <NAME>: DESCRIPTION *)
        variables;
      QUERY
  .
  ```

  The main difference is the introduction of a name and description enclosed in comments. In ProVerif, queries are not defined by name, making it slightly challenging to read the analysis results. With the `NAME` enclosed in angle brackets, both the Paralyzer tool and the analysts can better manage the results of each query. The `NAME` will be also used in creating a result folder and output.

- **Attacker**: In line 225 of the `ENC.pv` file,  `(* <ATTACKER> *)`, which is a placeholder reserved for the attacker process. Before processing, the Paralyzer will read the `attacker.pvl`, knowing the number of attackers. It will add all the processes into the main process file, resulting file in `./ATK`. These files will be involved in the analysis.

- **Result**: After a command is executed, Paralyzer records its running result and duration. It will save the results in `./paralyzer-result`and save the time in `./result-time.txt`  .In the result folder, the first level folder is named after the `CASE-ATTACKER`, and the second level folder is named after the query `NAME`. Each query folder contains a `output.log` and a `TRUE/FALSE/CANNOT/ESULT_NOT_FOUND.log`. The output.log saved the output of ProVerif, and the name  of `TRUE/FALSE/CANNOT/ESULT_NOT_FOUND.log` represents the result of the current query.

## Resulter

### How to use

The `Resulter.py` is the resulter. Before use it, please install **pandas** first (run `pip install pandas` in the terminal). You can run resulter with this command after finish running the paralyzer:

```
python Resulter.py
```

The Resulter will read and process all the results in the results folder, and finally generate an xlsx file. 

You can quickly view the analysis results by reading this table. The first column represents `CASE-ATTACKER`, corresponding to the first level folder in  `./paralyzer-result`. The remaining columns are the names of the query, and the contents of the values are the results of the query.

Resulter is called in Paralyzer. But you still can use the command to generate the xlsx file. 

