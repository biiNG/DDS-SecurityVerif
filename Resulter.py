import os
import pandas as pd


def extract_results(folder_path):
    # Create an empty result list to save the extracted results
    results = []

    # Traverse case folders
    for scene_folder in os.listdir(folder_path):
        scene_folder_path = os.path.join(folder_path, scene_folder)
        if os.path.isdir(scene_folder_path):
            # Traverse the query folder
            for situation_folder in os.listdir(scene_folder_path):
                situation_folder_path = os.path.join(scene_folder_path, situation_folder)
                if os.path.isdir(situation_folder_path):
                    # Find txt files named 'TRUE', 'FALSE', or 'CANNOT'
                    result = None
                    if len(os.listdir(situation_folder_path)) == 1:
                        with open(situation_folder_path+'/'+os.listdir(situation_folder_path)[0]) as file:
                            file.seek(0, 2)  # Set location to the end of the file
                            last_line_pos = file.tell() - 7
                            file.seek(last_line_pos)
                            last_line = file.readline()
                            if last_line.strip() == "query.":
                                result = 'CANNOT'
                    else:
                        for file_name in os.listdir(situation_folder_path):
                            file_name_without_extension = os.path.splitext(file_name)[0]
                            if file_name_without_extension == 'output':
                                continue
                            else:
                                result = file_name_without_extension
                                break

                    # Extract result and add it to the result list
                    if result:
                        results.append((scene_folder, situation_folder, result))
                    else:
                        results.append((scene_folder, situation_folder, 'UNPROVEN'))

    # Convert the result list to DataFrame and save it as a xlsx file
    df = pd.DataFrame(results, columns=["mode-attacker", "query", "result"])
    pivot_df = df.pivot(index="mode-attacker", columns="query", values="result")
    pivot_df.insert(0, "mode-attacker", pivot_df.index)
    pivot_df = pivot_df.reset_index(drop=True)
    pivot_df.to_excel("results.xlsx", index=False)


if __name__ == "__main__":
    folder_path = "./paralyzer-result/"
    extract_results(folder_path)
