package com.acme.flow;

public class FlowService {
    public String start(String input) {
        // validate(input) and finish(input) are comment decoys.
        String decoy = "Audit.record(input)";
        Audit.record(input);
        return validate(input);
    }

    private String validate(String input) {
        return finish(input);
    }

    private String finish(String input) {
        return input;
    }
}
