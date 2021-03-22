from apps.users.serializers import UserSerializer
from apps.visits.models import Visit
from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class VisitSerializer(serializers.ModelSerializer):
    authors = UserSerializer(many=True)
    author_ids = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True,
        source="authors",
        many=True,
        required=False,
    )

    def validate(self, data):
        if data.get("author_ids", None) and data.get("authors", None):
            raise serializers.ValidationError(
                "Either author_ids or authors should be provided"
            )
        return data

    def get_authors(self, validated_data):
        try:
            authors_data = validated_data.pop("authors")
        except KeyError:
            return []

        author_emails = [author_data["email"] for author_data in authors_data]
        authors = []

        for author_email in author_emails:
            author, _ = User.objects.get_or_create(email=author_email)
            authors.append(author)

        return authors

    def create(self, validated_data):
        authors = self.get_authors(validated_data)
        visit = Visit.objects.create(**validated_data)
        visit.authors.set(authors)

        return visit

    class Meta:
        model = Visit
        fields = "__all__"
