# # Tests for session queries

# from uuid_extensions import uuid7
# from ward import test

# from agents_api.autogen.openapi_model import (
#     CreateOrUpdateSessionRequest,
#     CreateSessionRequest,
#     Session,
# )
# from agents_api.queries.session.count_sessions import count_sessions
# from agents_api.queries.session.create_or_update_session import create_or_update_session
# from agents_api.queries.session.create_session import create_session
# from agents_api.queries.session.delete_session import delete_session
# from agents_api.queries.session.get_session import get_session
# from agents_api.queries.session.list_sessions import list_sessions
# from tests.fixtures import (
#     cozo_client,
#     test_agent,
#     test_developer_id,
#     test_session,
#     test_user,
# )

# MODEL = "gpt-4o-mini"


# @test("query: create session")
# def _(
#     client=cozo_client, developer_id=test_developer_id, agent=test_agent, user=test_user
# ):
#     create_session(
#         developer_id=developer_id,
#         data=CreateSessionRequest(
#             users=[user.id],
#             agents=[agent.id],
#             situation="test session about",
#         ),
#         client=client,
#     )


# @test("query: create session no user")
# def _(client=cozo_client, developer_id=test_developer_id, agent=test_agent):
#     create_session(
#         developer_id=developer_id,
#         data=CreateSessionRequest(
#             agents=[agent.id],
#             situation="test session about",
#         ),
#         client=client,
#     )


# @test("query: get session not exists")
# def _(client=cozo_client, developer_id=test_developer_id):
#     session_id = uuid7()

#     try:
#         get_session(
#             session_id=session_id,
#             developer_id=developer_id,
#             client=client,
#         )
#     except Exception:
#         pass
#     else:
#         assert False, "Session should not exist"


# @test("query: get session exists")
# def _(client=cozo_client, developer_id=test_developer_id, session=test_session):
#     result = get_session(
#         session_id=session.id,
#         developer_id=developer_id,
#         client=client,
#     )

#     assert result is not None
#     assert isinstance(result, Session)


# @test("query: delete session")
# def _(client=cozo_client, developer_id=test_developer_id, agent=test_agent):
#     session = create_session(
#         developer_id=developer_id,
#         data=CreateSessionRequest(
#             agent=agent.id,
#             situation="test session about",
#         ),
#         client=client,
#     )

#     delete_session(
#         session_id=session.id,
#         developer_id=developer_id,
#         client=client,
#     )

#     try:
#         get_session(
#             session_id=session.id,
#             developer_id=developer_id,
#             client=client,
#         )
#     except Exception:
#         pass

#     else:
#         assert False, "Session should not exist"


# @test("query: list sessions")
# def _(client=cozo_client, developer_id=test_developer_id, session=test_session):
#     result = list_sessions(
#         developer_id=developer_id,
#         client=client,
#     )

#     assert isinstance(result, list)
#     assert len(result) > 0


# @test("query: count sessions")
# def _(client=cozo_client, developer_id=test_developer_id, session=test_session):
#     result = count_sessions(
#         developer_id=developer_id,
#         client=client,
#     )

#     assert isinstance(result, dict)
#     assert result["count"] > 0


# @test("query: create or update session")
# def _(
#     client=cozo_client, developer_id=test_developer_id, agent=test_agent, user=test_user
# ):
#     session_id = uuid7()

#     create_or_update_session(
#         session_id=session_id,
#         developer_id=developer_id,
#         data=CreateOrUpdateSessionRequest(
#             users=[user.id],
#             agents=[agent.id],
#             situation="test session about",
#         ),
#         client=client,
#     )

#     result = get_session(
#         session_id=session_id,
#         developer_id=developer_id,
#         client=client,
#     )

#     assert result is not None
#     assert isinstance(result, Session)
#     assert result.id == session_id
