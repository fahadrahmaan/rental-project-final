import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .models import Homestay

def get_similar_homestays(homestay_id, top_n=3):
    target = Homestay.objects.get(id=homestay_id)

    # Try to find others in the same location first
    homestays = Homestay.objects.exclude(id=homestay_id)
    df = pd.DataFrame(list(homestays.values('id', 'name', 'location', 'property_type')))

    if df.empty:
        return []

    df['combined'] = df['location'] + ' ' + df['property_type']
    target_combined = target.location + ' ' + target.property_type

    # Append target to DataFrame for TF-IDF comparison
    df.loc[-1] = {
        'id': target.id,
        'name': target.name,
        'location': target.location,
        'property_type': target.property_type,
        'combined': target_combined
    }
    df.index = df.index + 1
    df = df.sort_index()

    tfidf = TfidfVectorizer()
    tfidf_matrix = tfidf.fit_transform(df['combined'])
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

    target_index = df.index[df['id'] == target.id][0]
    similarity_scores = list(enumerate(cosine_sim[target_index]))

    # Sort and get top N (skip self)
    sorted_similar = sorted(similarity_scores, key=lambda x: x[1], reverse=True)[1:top_n+1]
    similar_indices = [i[0] for i in sorted_similar]

    recommendations = []
    for i in similar_indices:
        row = df.iloc[i]
        reason = []

        if row['location'] == target.location:
            reason.append(f"Also in {target.location}")
        if row['property_type'] == target.property_type:
            reason.append(f"Also a {target.property_type.title()}")

        recommendations.append({
            'homestay': Homestay.objects.get(id=row['id']),
            'reason': ' & '.join(reason) if reason else "Similar features"
        })

    return recommendations

