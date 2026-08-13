package com.acme.flow;

public class FlowService {
    public String start(String input) {
        Audit.record(input);
        return normalize(input);
    }

    private String normalize(String input) {
        return validate(input);
    }

    private String validate(String input) {
        return finish(input);
    }

    private String finish(String input) {
        return input;
    }
}
