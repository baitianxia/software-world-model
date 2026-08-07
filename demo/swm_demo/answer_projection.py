from __future__ import annotations

from swm_demo.agent_contract import AgentTask, AnswerClaim


def claims_from_use_case_result(
    task: AgentTask, result: dict[str, object]
) -> tuple[AnswerClaim, ...]:
    if task.use_case.endswith("-view") and task.use_case != "structure-view":
        return tuple(
            AnswerClaim(
                text=str(item["statement"]),
                knowledge_reference_ids=(str(item["inference_id"]),),
            )
            for item in result.get("items", [])
        )

    if task.use_case == "endpoint-structure":
        if result.get("status") != "READY":
            return ()
        modules = ", ".join(
            str(item["name"]) for item in result.get("module", [])
        )
        controllers = ", ".join(
            str(item["name"]) for item in result.get("controller_methods", [])
        )
        services = ", ".join(
            str(item["name"]) for item in result.get("service_methods", [])
        )
        implementations = ", ".join(
            str(item["name"])
            for item in result.get("implementation_methods", [])
        )
        text = (
            f"{result['endpoint']['name']} 位于 {modules}，调用链为 "
            f"{controllers} → {services} → {implementations}。"
        )
        return (
            AnswerClaim(
                text=text,
                knowledge_reference_ids=tuple(
                    str(item) for item in result.get("knowledge_references", [])
                ),
            ),
        )

    if task.use_case == "structure-view":
        module_names = ", ".join(
            str(item["name"]) for item in result.get("modules", [])
        )
        dependency_count = len(result.get("dependencies", []))
        references = [
            str(item["fact_id"])
            for item in (*result.get("modules", []), *result.get("dependencies", []))
        ]
        return (
            AnswerClaim(
                text=f"系统包含模块：{module_names}；本地依赖关系共 {dependency_count} 条。",
                knowledge_reference_ids=tuple(sorted(set(references))),
            ),
        )
    return ()
