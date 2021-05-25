using JuMP, Cbc, NPZ

function Solve_func(year, tol)

	println("Solving weights for $year ...\n\n")

	# we only solve the weights for years where the targets have changed. If the
	# targets have not changed, we don't write the _input.npz file
	if isfile(string(year, "_input.npz"))
		array = npzread(string(year, "_input.npz"))
	else
		println("Skipping solver for $year \n")
		return nothing
	end

	A1 = array["A1"]
	A2 = array["A2"]
	b = array["b"]

	model = Model(Cbc.Optimizer)
	set_optimizer_attribute(model, "logLevel", 1)
	N = size(A1)[2]

	@variable(model, r[1:N] >= 0)
	@variable(model, s[1:N] >= 0)

	@objective(model, Min, sum(r[i] + s[i] for i in 1:N))

	# bound on top by tolerance
	@constraint(model, [i in 1:N], r[i] + s[i] <= tol)

	# Ax = b
	@constraint(model, [i in 1:length(b)], sum(A1[i,j] * r[j] + A2[i,j] * s[j]
		                          for j in 1:N) == b[i])


	optimize!(model)
	termination_status(model)

	r_vec = value.(r)
	s_vec = value.(s)

	npzwrite(string(year, "_output.npz"), Dict("r" => r_vec, "s" => s_vec))

	println("\n")

end



year_list = [x for x in 2012:2030]
tol_list = [0.40, 0.38, 0.35, 0.33, 0.30, 0.45, 0.45,
			0.45, 0.45, 0.45, 0.45, 0.45, 0.45, 0.45,
			0.45, 0.45, 0.45, 0.45, 0.45]

# Run solver function for all years and tolerances (in order)
for i in zip(year_list, tol_list)
	Solve_func(i[1], i[2])
end
