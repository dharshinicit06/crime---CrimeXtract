# Architecture

## Hybrid SQL + LLM

User Message -> Intent Classifier -> ServiceRouter -> Module Service -> MySQL -> Structured Data -> Gemini Summary -> Response

### Key Principles
1. Intent classification is rule-based (no Gemini cost)
2. ServiceRouter delegates, never queries SQL
3. Gemini only summarizes retrieved data
4. Kannada via translation wrappers
5. Demo Mode as parallel routing layer
