import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from mangum import Mangum


from routes.company import (
    all_company,
    company_by_id,
    edit_company_comment,
    edit_company_relevance,
    hide_companies,
)
from routes.signals import all_signals, signal_by_id
from routes.search import search_by_id, all_search
from routes.people import (
    people_by_id,
    all_people,
    hide_people,
    edit_person_comment,
    edit_person_relevance,
)
from routes.list import (
    create_list,
    delete_list,
    modify_entities_in_list,
    get_all_lists,
    get_all_entities_by_list,
)

app = FastAPI(swagger_ui_parameters={"displayRequestDuration": True})
handler = Mangum(app)

is_lambda = os.environ.get("AWS_LAMBDA_FUNCTION_NAME") is not None

if not is_lambda:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/")
def read_root():
    return RedirectResponse(url="/docs")


app.include_router(all_company.router)
app.include_router(company_by_id.router)
app.include_router(hide_companies.router)
app.include_router(edit_company_comment.router)
app.include_router(edit_company_relevance.router)

app.include_router(all_people.router)
app.include_router(people_by_id.router)
app.include_router(hide_people.router)
app.include_router(edit_person_comment.router)
app.include_router(edit_person_relevance.router)

app.include_router(all_signals.router)
app.include_router(signal_by_id.router)

app.include_router(all_search.router)
app.include_router(search_by_id.router)

app.include_router(get_all_lists.router)
app.include_router(get_all_entities_by_list.router)
app.include_router(create_list.router)
app.include_router(delete_list.router)
app.include_router(modify_entities_in_list.router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
