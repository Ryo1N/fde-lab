import { layout, route, type RouteConfig } from "@react-router/dev/routes";

export default [
  route("/admin-login", "routes/admin_login_form.tsx"),
  layout("layouts/default.tsx", [
    route("/", "routes/home.tsx"),
    route("job-boards", "routes/job_boards.tsx"),
    route("job-boards/new", "routes/new_job_board.tsx"),
    route("job-boards/:jobBoardId/edit", "routes/update_job_board.tsx"),
    route("job-boards/:jobBoardId/job-posts", "routes/job_posts.tsx"),
    route("/job-posts/:jobPostId/application", "routes/new_job_post_application.tsx")
  ])
] satisfies RouteConfig;

