from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import Quest, QuestSubmission
from .serializers import QuestListSerializer, QuestDetailSerializer, QuestSubmissionSerializer

class QuestListView(generics.ListAPIView):
    """
    Lists quests, optionally filtered by skill_id.
    """
    serializer_class = QuestListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Quest.objects.all()
        skill_id = self.request.query_params.get('skill_id')
        if skill_id:
            queryset = queryset.filter(skill_id=skill_id)
        return queryset

class QuestDetailView(generics.RetrieveAPIView):
    """
    Retrieve full quest details.
    """
    queryset = Quest.objects.all()
    serializer_class = QuestDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

class QuestSubmitView(APIView):
    """
    Handles quest code submission.
    Creates a pending submission and triggers evaluation.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        quest = get_object_or_404(Quest, pk=pk)
        serializer = QuestSubmissionSerializer(data=request.data)
        
        if serializer.is_valid():
            submission = serializer.save(user=request.user, quest=quest, status='pending')
            
            # TODO: Trigger Celery chain for Phase 9
            # evaluate_submission.delay(submission.id)
            
            return Response({
                "submission_id": submission.id,
                "status": submission.status,
                "message": "Submission received and queued for evaluation."
            }, status=status.HTTP_201_CREATED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
