using NPZ, JuMP, Cbc, Tulip

function Solve_func(year, tol)

	println("\nSolving weights for $year ...\n")

	solver = "Tulip"  # Tulip, Cbc
	Tulip_max_iter = 100  # 100 default, 500 seems good enough

	println("Using solver: ", solver)
	if solver == "Tulip"
		model = Model(Tulip.Optimizer)
		set_optimizer_attribute(model, "OutputLevel", 1)  # 0=disable output (default), 1=show iterations
		set_optimizer_attribute(model, "IPM_IterationsLimit", Tulip_max_iter)  # default 100
	elseif solver == "Cbc"
		model = Model(Cbc.Optimizer)
		set_optimizer_attribute(model, "logLevel", 1)
		# I have not figured out option to limit iterations
	else
		println("ERROR! Solver must be Tulip or Cbc.")
	end

	array = npzread(string(year, "_input.npz"))

	A1 = array["A1"]
	A2 = array["A2"]
	b = array["b"]

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
	println("Termination status: ", termination_status(model))
	println("Objective: ", objective_value(model))
	println("\nSolver used was: ", solver_name(model), "\n")

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
