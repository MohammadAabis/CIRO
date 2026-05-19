import 'package:go_router/go_router.dart';
import 'package:ciro_app/features/dashboard/presentation/pages/dashboard_page.dart';

final GoRouter appRouter = GoRouter(
  initialLocation: '/',
  routes: [
    GoRoute(
      path: '/',
      name: 'dashboard',
      builder: (context, state) => const DashboardPage(),
    ),
    // TODO: add crisis detail, resource map, simulation routes
  ],
);
