# AI Tutor State Machine Diagram

## Full System Flow (LangGraph)
stateDiagram-v2
    [*] --> Planner: student_input received

    state Planner {
        [*] --> BuildContext: query + conversation_history
        BuildContext --> LLM_Planning: enable_llm = true
        BuildContext --> Heuristic_Planning: enable_llm = false

        LLM_Planning --> Parse_LLM: LLM response received
        Parse_LLM --> Return_Plan: parsing succeeded
        Parse_LLM --> Heuristic_Planning: parsing failed & force_llm = false
        Parse_LLM --> Raise_Error: parsing failed & force_llm = true

        Heuristic_Planning --> Return_Plan: heuristic matched
        Heuristic_Planning --> Fallback_Reject: no match found

        Fallback_Reject --> Return_Plan: default reject plan
    }

    Planner --> Router: plan created

    state Router {
        [*] --> Check_Plan
        Check_Plan --> Get_Subtask: plan exists
        Check_Plan --> Mark_End: no plan

        Get_Subtask --> Select_Task: idx < subtasks.length
        Get_Subtask --> Mark_End: idx >= subtasks.length

        Select_Task --> Route_Decision: current_subtask set
        Mark_End --> Route_Decision: _routing_decision = __end__
    }

    Router --> Tutor: task = "explain"
    Router --> Math: task = "solve"
    Router --> Reject: task = "reject" OR (task = "chat" & message = "off_topic")
    Router --> Feedback: no more subtasks OR _routing_decision = __end__

    state Tutor {
        [*] --> Extract_Topic
        Extract_Topic --> RAG_Retrieval
        RAG_Retrieval --> Generate_Response
        Generate_Response --> Append_Output
    }

    state Math {
        [*] --> Extract_Problem
        Extract_Problem --> Solve_Problem
        Solve_Problem --> Format_Steps
        Format_Steps --> Append_Output
    }

    state Reject {
        [*] --> Generate_Rejection_Message
        Generate_Rejection_Message --> Set_Fallback_Flag
    }

    Tutor --> Router: subtask completed (loop for next subtask)
    Math --> Router: subtask completed (loop for next subtask)
    Reject --> Feedback: rejection handled

    state Feedback {
        [*] --> Mark_Complete
        Mark_Complete --> Set_Final_Response
    }

    Feedback --> [*]: final_response returned
