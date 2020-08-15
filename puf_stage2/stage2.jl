using Pandas
include("dataprep.jl")
# include("solver.jl")

puf = read_csv(joinpath(@__DIR__,"..","puf_data","cps-matched-puf.csv"))
Stage_I_factors = read_csv(joinpath(@__DIR__,"..","puf_stage1","Stage_I_factors_transpose.csv"),
                      index_col = 0)
Stage_II_targets = read_csv(joinpath(@__DIR__,"..","puf_stage1","Stage_II_targets.csv"),
                        index_col = 0)

# Use the matched_weight variable in CPS as the final weight
puf["s006"] = puf["matched_weight"] * 100



z = DataFrame()
z["WT2011"] = puf["s006"]

# Execute stage2 logic for each year using a year-specific LP tolerance
# function create_weights(puf, Stage_I_factors, Stage_II_targets, year, tol)
    # col_name = string("WT", year)
# end

tol_list = [0.40, 0.38, 0.35, 0.33, 0.30, 0.37, 0.38, 0.38, 0.39, 0.39, 0.38, 0.40, 0.39, 0.41, 0.41, 0.42, 0.42, 0.42, 0.42]
year_list = [2012:1:2030;]

function test_func(puf, Stage_I_factors, Stage_II_targets, year, tol)
	Dataprep(puf, Stage_I_factors, Stage_II_targets, year)
end

# # run function for all tolerance levels and years (in sequential order) using broadcasting
# create_weights.(puf, Stage_I_factors, Stage_II_targets, year_list, tol_list)

# test_func.(puf, Stage_I_factors, Stage_II_targets, year_list, tol_list)
test_func(puf, Stage_I_factors, Stage_II_targets, 2012, 0.4)


# z = z.round(0).astype('int64') # python code

# this can be combined before adding to dataframe using round.(Int64, [array])
# ^^^ *** NOTE THE BROADCASTING OPERATOR ***

# to_csv(z, joinpath(@__DIR__, "puf_weights.csv.gz"), index=false, compression = "gzip") # "false" MUST be LOWERcase