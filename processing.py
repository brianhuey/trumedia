from season import Season

run_exp_hits = 'data/run_exp_hits_2015.pickle'
run_exp_count = 'data/run_exp_count_2015.pickle'
heatmap = 'data/heatmaps_2015.pickle'

season = Season(run_exp_hits, run_exp_count, lastSeason=heatmap)

filename = 'data/2016.csv'
output_file = 'data/2016_processed.csv'

season.process_file(filename, output_file)