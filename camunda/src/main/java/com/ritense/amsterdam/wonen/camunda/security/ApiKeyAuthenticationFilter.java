package com.ritense.amsterdam.wonen.camunda.security;

import javax.servlet.*;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.springframework.security.core.authority.AuthorityUtils;
import org.springframework.security.core.context.SecurityContextHolder;

import java.io.IOException;

public class ApiKeyAuthenticationFilter implements Filter {

    private final String apiKey;

    public ApiKeyAuthenticationFilter(String apiKey) {
        this.apiKey = apiKey;
    }


    @Override
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
            throws IOException, ServletException
    {
        if(request instanceof HttpServletRequest && response instanceof HttpServletResponse) {
            String getApiKey = getApiKey((HttpServletRequest) request);
            if(getApiKey != null) {
                if(getApiKey.equals(apiKey)) {
                    ApiKeyAuthenticationToken apiToken = new ApiKeyAuthenticationToken(getApiKey, AuthorityUtils.NO_AUTHORITIES);
                    SecurityContextHolder.getContext().setAuthentication(apiToken);
                } else {
                    HttpServletResponse httpResponse = (HttpServletResponse) response;
                    httpResponse.setStatus(401);
                    httpResponse.getWriter().write("Invalid API Key");
                    return;
                }
            }
        }

        chain.doFilter(request, response);

    }

    private String getApiKey(HttpServletRequest httpRequest) {
        String getApiKey = null;

        String authHeader = httpRequest.getHeader("API_KEY");
        if(authHeader != null) {
            getApiKey = authHeader.trim();
        }

        return getApiKey;
    }
}
