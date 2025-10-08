from sklearn.datasets import fetch_20newsgroups
from sklearn.naive_bayes import MultinomialNB
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.feature_extraction.text import CountVectorizer

# Define the category map
category_map = {'talk.politics.misc': 'Politics', 'rec.autos': 'Autos', 
        'rec.sport.hockey': 'Hockey', 'sci.electronics': 'Electronics', 
        'sci.med': 'Medicine'}

# Get the training dataset
training_data = fetch_20newsgroups(subset='train', 
        categories=category_map.keys(), shuffle=True, random_state=5)
#Let us check the data
print("\n".join(training_data.data[0].split("\n")[:50]))
print("\n".join(training_data.data[1].split("\n")[:50]))
print("\n".join(training_data.data[2].split("\n")[:50]))
print("\n".join(training_data.data[3].split("\n")[:50]))
print("\n".join(training_data.data[4].split("\n")[:50]))
print("\n".join(training_data.data[5].split("\n")[:50]))
#Check the category
print(training_data.target_names[training_data.target[0]])
print(training_data.target_names[training_data.target[1]])
print(training_data.target_names[training_data.target[2]])
print(training_data.target_names[training_data.target[3]])
print(training_data.target_names[training_data.target[4]])
print(training_data.target_names[training_data.target[5]])
for t in training_data.target[:100]:
     print(training_data.target_names[t])
#chck how many files
len(training_data.filenames)
# Build a count vectorizer and extract term counts 
#Text preprocessing, tokenizing and filtering of stopwords are all included in
#CountVectorizer, which builds a dictionary of features and transforms documents
# to feature vectors:
count_vectorizer = CountVectorizer()
train_tc = count_vectorizer.fit_transform(training_data.data)
print("\nDimensions of training data:", train_tc.shape)
#Occurrence count is a good start but there is an issue: longer documents will have
# higher average count values than shorter documents, even though they might talk 
#about the same topics.
#Another refinement on top of tf is to downscale weights for words that occur
# in many documents in the corpus and are therefore less informative than those 
#that occur only in a smaller portion of the corpus.

#This downscaling is called tf–idf for “Term Frequency times Inverse Document Frequency”.
# Create the tf-idf transformer
tfidf = TfidfTransformer()
train_tfidf = tfidf.fit_transform(train_tc)
type(train_tfidf)
# Train a Multinomial Naive Bayes classifier
classifier = MultinomialNB().fit(train_tfidf, training_data.target)

# Define test data 
input_data = [
    'You need to be careful with cars when you are driving on slippery roads', 
    'A lot of devices can be operated wirelessly',
    'Players need to be careful when they are close to goal posts',
    'Political debates help us understand the perspectives of both sides',
    'A feel pain every morning',
    'I got a speed ticket this morning comming to work'
]

# Transform input data using count vectorizer
input_tc = count_vectorizer.transform(input_data)
type(input_tc)
print(input_tc)
# Transform vectorized data using tfidf transformer
input_tfidf = tfidf.transform(input_tc)
type(input_tfidf)
print(input_tfidf)
# Predict the output categories
predictions = classifier.predict(input_tfidf)

# Print the outputs
for sent, category in zip(input_data, predictions):
    print('\nInput:', sent, '\nPredicted category:', \
            category_map[training_data.target_names[category]])

