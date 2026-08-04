def refinement_controller(evaluation):
    """
    Decides whether to continue the loop and how to refine the next generation.
    """

    # If evaluator says stop, we stop
    if evaluation.get("stop", False):
        return {
            "done": True,
            "generation_params": {}
        }

    # Otherwise refine based on suggestions
    suggestions = evaluation.get("suggestions", "")
    missing_types = evaluation.get("missing_types", [])

    return {
        "done": False,
        "generation_params": {
            "suggestions": suggestions,
            "missing_types": missing_types
        }
    }
