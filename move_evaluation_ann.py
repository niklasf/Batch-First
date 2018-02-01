import tensorflow as tf

import ann_creation_helper as ann_h
from functools import reduce


tf.logging.set_verbosity(tf.logging.INFO)




def main(unused_param):
    """
    Set up the data pipelines, create the computational graph, train the model, and evaluate the results.
    """
    SAVE_MODEL_DIR = "/srv/tmp/current/move_ordering_full_data_17"
    TRAINING_FILENAMES = ["/srv/databases/chess_engine/move_gen/full_training_data_part_" + str(num) + ".tfrecords" for num in range(9)]
    VALIDATION_FILENAMES = ["/srv/databases/chess_engine/move_gen/full_training_data_part_9.tfrecords"]
    TRAIN_OP_SUMMARIES = ["gradient_norm", "gradients"]
    NUM_OUTPUTS = 1792
    DENSE_SHAPE =  [300,300,500]#[800,800,800]
    OPTIMIZER = 'Adam'
    TRAINING_BATCH_SIZE = 250
    VALIDATION_BATCH_SIZE = 2000
    LOG_ITERATION_INTERVAL =2000
    LEARNING_RATE = .0001#.000002
    MAKE_CNN_MODULES_TRAINABLE = True


    INCEPTION_MODULES = [
        [
            [[32,2],[64,2]],
            [[64,3]]],
        [
            [[64,1]],
            [[16,1], [32,1,6]],
            [[16,1], [32,6,1]]]]  #Output of 1536 neurons



    BATCHES_IN_TRAINING_EPOCH = 3870000 // (TRAINING_BATCH_SIZE)
    BATCHES_IN_VALIDATION_EPOCH = 430000// VALIDATION_BATCH_SIZE


    learning_decay_function = lambda gs  : tf.train.exponential_decay(LEARNING_RATE,
                                                                      global_step=gs,
                                                                      decay_steps=4*BATCHES_IN_TRAINING_EPOCH,
                                                                      decay_rate=0.96,
                                                                      staircase=True)

    print(BATCHES_IN_TRAINING_EPOCH)
    print(BATCHES_IN_VALIDATION_EPOCH)


    # Create the Estimator
    classifier = tf.estimator.Estimator(
        model_fn=ann_h.move_gen_cnn_model_fn,
        model_dir=SAVE_MODEL_DIR,
        config=tf.estimator.RunConfig().replace(
            save_checkpoints_steps=LOG_ITERATION_INTERVAL,
            save_summary_steps=LOG_ITERATION_INTERVAL),
            # session_config=tf.ConfigProto(log_device_placement=True)),
        params={
            "dense_shape": DENSE_SHAPE,
            "optimizer": OPTIMIZER,
            "num_outputs": NUM_OUTPUTS,
            "log_interval": LOG_ITERATION_INTERVAL,
            "model_dir": SAVE_MODEL_DIR,
            "inception_modules" : INCEPTION_MODULES,
            "learning_rate": LEARNING_RATE,
            "train_summaries": TRAIN_OP_SUMMARIES,
            "learning_decay_function" : learning_decay_function,
            "trainable_cnn_modules" : MAKE_CNN_MODULES_TRAINABLE,
        })



    validation_hook = ann_h.ValidationRunHook(
        step_increment=BATCHES_IN_TRAINING_EPOCH,
        estimator=classifier,
        input_fn_creator=lambda: ann_h.move_gen_one_hot_create_tf_records_input_data_fn(VALIDATION_FILENAMES,VALIDATION_BATCH_SIZE,repeat=False,shuffle=False),
        temp_num_steps_in_epoch=BATCHES_IN_VALIDATION_EPOCH,
        recall_input_fn_creator_after_evaluate=True)

    classifier.train(
        input_fn=ann_h.move_gen_one_hot_create_tf_records_input_data_fn(
            TRAINING_FILENAMES,
            TRAINING_BATCH_SIZE),
        hooks=[validation_hook],
        # max_steps=1,
    )


    classifier.export_savedmodel(
        SAVE_MODEL_DIR + "/whites_turn",
        serving_input_receiver_fn=ann_h.serving_input_reciever_legal_moves_fn(True),
    )

    classifier.export_savedmodel(
        SAVE_MODEL_DIR + "/blacks_turn",
        serving_input_receiver_fn=ann_h.serving_input_reciever_legal_moves_fn(False),
    )





if __name__ == "__main__":
    tf.app.run()