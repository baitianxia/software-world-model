package com.acme.flow;

public class FlowService {
    public String start(String input) {
        return finish(input);
    }

    private String finish(String input) {
        return input;
    }

    private String finish(Object input) {
        return "unsupported-overload";
    }
}
