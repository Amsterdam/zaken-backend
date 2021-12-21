from apps.users.serializers import UserSerializer
from apps.visits.models import Visit
from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class VisitSerializer(serializers.ModelSerializer):
    authors = UserSerializer(many=True, required=False)
    author_ids = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True,
        source="authors",
        many=True,
        required=False,
    )

    def get_authors(self, validated_data):
        authors_data = validated_data.pop("authors")
        authors = []

        for author in authors_data:
            if isinstance(author, User):
                authors.append(author)
            else:
                author_email = author.get("email", "")
                author = User.objects.filter(email__iexact=author_email).first()
                if author:
                    authors.append(author)

        return authors

    def create(self, validated_data):
        authors = self.get_authors(validated_data)
        visit = Visit.objects.create(**validated_data)
        visit.authors.set(authors)

        return visit

    class Meta:
        model = Visit
        exclude = ("case_user_task_id",)
