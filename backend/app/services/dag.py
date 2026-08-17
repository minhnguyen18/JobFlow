def validate_dag(steps):

    graph = {
        step.id: step.depends_on
        for step in steps
    }

    step_ids = set(graph.keys())

    for step in steps:

        for dependency in step.depends_on:

            if dependency not in step_ids:

                raise ValueError(
                    f"Unknown dependency "
                    f"{dependency} "
                    f"for step {step.id}"
                )

    visiting = set()
    visited = set()

    def visit(node):

        if node in visiting:
            raise ValueError(
                "Workflow contains a cycle"
            )

        if node in visited:
            return

        visiting.add(node)

        for dependency in graph[node]:
            visit(dependency)

        visiting.remove(node)

        visited.add(node)

    for node in graph:
        visit(node)