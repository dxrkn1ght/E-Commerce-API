from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from products.models import Product
from .models import Review, ProductLike
from .serializers import ReviewCreateSerializer, ReviewSerializer, ProductLikeSerializer


class ProductReviewCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ReviewCreateSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['product_id'] = self.kwargs['id']
        return context

    def create(self, request, *args, **kwargs):
        # Check if product exists
        product = get_object_or_404(Product, id=self.kwargs['id'])

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review = serializer.save()

        return Response({
            'success': True,
            'data': ReviewSerializer(review).data
        }, status=status.HTTP_201_CREATED)


class ProductLikeToggleView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        product = get_object_or_404(Product, id=self.kwargs['id'])
        user = request.user

        like_obj, created = ProductLike.objects.get_or_create(
            user=user,
            product=product
        )

        if not created:
            # Unlike - remove the like
            like_obj.delete()
            liked = False
        else:
            # Like - already created above
            liked = True

        return Response({
            'success': True,
            'data': {
                'liked': liked,
                'likes_count': product.likes.count()
            }
        })