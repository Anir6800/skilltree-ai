"""
SkillTree AI - Peer Code Review System Views
API endpoints for sharing, viewing, and reviewing solutions.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, F
from django.utils import timezone
from difflib import unified_diff

from quests.models import QuestSubmission, SharedSolution, SolutionComment, Quest
from quests.serializers import (
    SharedSolutionDetailSerializer,
    SharedSolutionListSerializer,
    SolutionCommentSerializer,
)


class ShareSolutionView(APIView):
    """
    POST /api/solutions/{submission_id}/share/
    Share a passed submission as a solution.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, submission_id):
        submission = get_object_or_404(QuestSubmission, id=submission_id, user=request.user)

        if submission.status != 'passed':
            return Response(
                {'error': 'Only passed submissions can be shared'},
                status=status.HTTP_400_BAD_REQUEST
            )

        is_anonymous = request.data.get('is_anonymous', False)

        shared_solution, created = SharedSolution.objects.get_or_create(
            submission=submission,
            defaults={'is_anonymous': is_anonymous}
        )

        if not created:
            return Response(
                {'error': 'This solution is already shared'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = SharedSolutionDetailSerializer(shared_solution, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SolutionsListView(APIView):
    """
    GET /api/solutions/?quest_id=X&sort=top|new|fastest
    Get paginated list of shared solutions.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        quest_id = request.query_params.get('quest_id')
        sort = request.query_params.get('sort', 'new')
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))

        queryset = SharedSolution.objects.select_related(
            'submission__user',
            'submission__quest'
        ).prefetch_related('upvotes', 'comments')

        if quest_id:
            queryset = queryset.filter(submission__quest_id=quest_id)

        if sort == 'top':
            queryset = queryset.annotate(upvote_count=Count('upvotes')).order_by('-upvote_count', '-shared_at')
        elif sort == 'fastest':
            queryset = queryset.annotate(
                solve_time=F('shared_at') - F('submission__created_at')
            ).order_by('solve_time', '-shared_at')
        else:
            queryset = queryset.order_by('-shared_at')

        total_count = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size
        solutions = queryset[start:end]

        serializer = SharedSolutionListSerializer(
            solutions,
            many=True,
            context={'request': request}
        )

        return Response({
            'count': total_count,
            'page': page,
            'page_size': page_size,
            'results': serializer.data
        })


class SolutionDetailView(APIView):
    """
    GET /api/solutions/{id}/
    Get detailed view of a solution with comments.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, solution_id):
        solution = get_object_or_404(SharedSolution, id=solution_id)

        solution.views_count = F('views_count') + 1
        solution.save(update_fields=['views_count'])

        serializer = SharedSolutionDetailSerializer(solution, context={'request': request})
        return Response(serializer.data)


class SolutionDiffView(APIView):
    """
    GET /api/solutions/{id}/diff/
    Get diff between shared solution and model solution.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, solution_id):
        solution = get_object_or_404(SharedSolution, id=solution_id)
        submission = solution.submission
        quest = submission.quest

        user_code = submission.code.split('\n')
        model_code = quest.starter_code.split('\n') if quest.starter_code else []

        diff_lines = []
        for line in unified_diff(model_code, user_code, lineterm=''):
            if line.startswith('+++') or line.startswith('---') or line.startswith('@@'):
                continue

            if line.startswith('+'):
                diff_lines.append({
                    'type': 'add',
                    'text': line[1:],
                })
            elif line.startswith('-'):
                diff_lines.append({
                    'type': 'remove',
                    'text': line[1:],
                })
            else:
                diff_lines.append({
                    'type': 'same',
                    'text': line[1:] if line else '',
                })

        return Response({
            'user_code': submission.code,
            'model_solution': quest.starter_code,
            'diff_lines': diff_lines,
            'language': submission.language,
        })


class UpvoteSolutionView(APIView):
    """
    POST /api/solutions/{id}/upvote/
    Toggle upvote on a solution (idempotent).
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, solution_id):
        solution = get_object_or_404(SharedSolution, id=solution_id)

        if solution.upvotes.filter(id=request.user.id).exists():
            solution.upvotes.remove(request.user)
            upvoted = False
        else:
            solution.upvotes.add(request.user)
            upvoted = True

        return Response({
            'upvoted': upvoted,
            'upvote_count': solution.get_upvote_count()
        })


class AddCommentView(APIView):
    """
    POST /api/solutions/{id}/comments/
    Add a comment to a solution.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, solution_id):
        solution = get_object_or_404(SharedSolution, id=solution_id)

        text = request.data.get('text', '').strip()
        parent_id = request.data.get('parent_id')

        if not text:
            return Response(
                {'error': 'Comment text is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(text) > 1000:
            return Response(
                {'error': 'Comment must be 1000 characters or less'},
                status=status.HTTP_400_BAD_REQUEST
            )

        parent = None
        if parent_id:
            parent = get_object_or_404(SolutionComment, id=parent_id, solution=solution)

        comment = SolutionComment.objects.create(
            solution=solution,
            author=request.user,
            text=text,
            parent=parent
        )

        serializer = SolutionCommentSerializer(comment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CommentsListView(APIView):
    """
    GET /api/solutions/{id}/comments/
    Get all comments for a solution (threaded).
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, solution_id):
        solution = get_object_or_404(SharedSolution, id=solution_id)

        root_comments = solution.comments.filter(parent__isnull=True).order_by('created_at')
        serializer = SolutionCommentSerializer(root_comments, many=True)

        return Response(serializer.data)


class DeleteCommentView(APIView):
    """
    DELETE /api/solutions/comments/{comment_id}/
    Delete a comment (only by author).
    """
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, comment_id):
        comment = get_object_or_404(SolutionComment, id=comment_id)

        if comment.author != request.user:
            return Response(
                {'error': 'You can only delete your own comments'},
                status=status.HTTP_403_FORBIDDEN
            )

        comment.delete()
        return Response({'message': 'Comment deleted'})


class UserSolutionsView(APIView):
    """
    GET /api/solutions/user/
    Get all solutions shared by the current user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        solutions = SharedSolution.objects.filter(
            submission__user=request.user
        ).select_related(
            'submission__user',
            'submission__quest'
        ).prefetch_related('upvotes', 'comments').order_by('-shared_at')

        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))

        total_count = solutions.count()
        start = (page - 1) * page_size
        end = start + page_size
        solutions_page = solutions[start:end]

        serializer = SharedSolutionListSerializer(
            solutions_page,
            many=True,
            context={'request': request}
        )

        return Response({
            'count': total_count,
            'page': page,
            'page_size': page_size,
            'results': serializer.data
        })
